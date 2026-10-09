#!/usr/bin/env python3
"""Validate a personas.json file produced by the search-persona-generator skill.

Usage:
    python3 validate_personas.py PERSONAS_JSON [--schema references/personas-schema.json]

Checks the file against personas-schema.json (a small built-in subset of JSON Schema, so no
third-party dependency is needed) and then applies rules the schema cannot express:

  * meta.persona_count equals the number of personas
  * persona names are unique
  * every services_matched entry appears in brand.services (case-insensitive substring match)
  * no query string is repeated across a persona's intent buckets
  * a persona with confidence "high" must cite at least two evidence items

Exit 0 when valid, 1 when not. Every problem is printed, one per line, prefixed with "FAIL".
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

DEFAULT_SCHEMA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "references", "personas-schema.json")


# --------------------------------------------------------------------------- tiny schema checker
def check(node, schema: dict, path: str, problems: list[str]) -> None:
    t = schema.get("type")
    if t == "object":
        if not isinstance(node, dict):
            problems.append(f"{path}: expected object, got {type(node).__name__}")
            return
        for key in schema.get("required", []):
            if key not in node:
                problems.append(f"{path}.{key}: missing required field")
        props = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for key in node:
                if key not in props:
                    problems.append(f"{path}.{key}: unexpected field")
        for key, sub in props.items():
            if key in node:
                check(node[key], sub, f"{path}.{key}", problems)
    elif t == "array":
        if not isinstance(node, list):
            problems.append(f"{path}: expected array, got {type(node).__name__}")
            return
        if "minItems" in schema and len(node) < schema["minItems"]:
            problems.append(f"{path}: needs at least {schema['minItems']} items, has {len(node)}")
        if "maxItems" in schema and len(node) > schema["maxItems"]:
            problems.append(f"{path}: allows at most {schema['maxItems']} items, has {len(node)}")
        item_schema = schema.get("items")
        if item_schema:
            for i, item in enumerate(node):
                check(item, item_schema, f"{path}[{i}]", problems)
    elif t == "string":
        if not isinstance(node, str):
            problems.append(f"{path}: expected string, got {type(node).__name__}")
            return
        if "minLength" in schema and len(node.strip()) < schema["minLength"]:
            problems.append(f"{path}: must not be empty")
        if "enum" in schema and node not in schema["enum"]:
            problems.append(f"{path}: '{node}' not one of {schema['enum']}")
        if "pattern" in schema and not re.search(schema["pattern"], node):
            problems.append(f"{path}: '{node}' does not match {schema['pattern']}")
    elif t == "integer":
        if not isinstance(node, int) or isinstance(node, bool):
            problems.append(f"{path}: expected integer, got {type(node).__name__}")
            return
        if "minimum" in schema and node < schema["minimum"]:
            problems.append(f"{path}: {node} below minimum {schema['minimum']}")
        if "maximum" in schema and node > schema["maximum"]:
            problems.append(f"{path}: {node} above maximum {schema['maximum']}")


# --------------------------------------------------------------------------- semantic rules
def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def semantic_rules(doc: dict, problems: list[str]) -> None:
    personas = doc.get("personas") or []
    meta = doc.get("meta") or {}
    if isinstance(meta.get("persona_count"), int) and meta["persona_count"] != len(personas):
        problems.append(f"meta.persona_count={meta['persona_count']} but {len(personas)} personas present")

    names = [p.get("name", "") for p in personas if isinstance(p, dict)]
    dupes = {n for n in names if names.count(n) > 1}
    for d in dupes:
        problems.append(f"personas: duplicate persona name '{d}'")

    services = [norm(s) for s in (doc.get("brand") or {}).get("services", []) if isinstance(s, str)]
    for i, p in enumerate(personas):
        if not isinstance(p, dict):
            continue
        for sm in p.get("services_matched", []):
            if not isinstance(sm, str):
                continue
            n = norm(sm)
            if not any(n in s or s in n for s in services):
                problems.append(f"personas[{i}].services_matched: '{sm}' is not in brand.services")

        sb = p.get("search_behavior") or {}
        seen: dict[str, str] = {}
        for bucket in ("informational_queries", "commercial_queries", "transactional_queries", "question_queries"):
            for q in sb.get(bucket, []) or []:
                if not isinstance(q, str):
                    continue
                k = norm(q)
                if k in seen and seen[k] != bucket:
                    problems.append(f"personas[{i}].search_behavior: query '{q}' appears in both {seen[k]} and {bucket}")
                seen.setdefault(k, bucket)

        if p.get("confidence") == "high" and len(p.get("evidence") or []) < 2:
            problems.append(f"personas[{i}]: confidence 'high' requires at least two evidence items")


def validate(doc, schema: dict) -> list[str]:
    problems: list[str] = []
    check(doc, schema, "$", problems)
    if isinstance(doc, dict):
        semantic_rules(doc, problems)
    return problems


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("personas_json")
    ap.add_argument("--schema", default=DEFAULT_SCHEMA)
    args = ap.parse_args(argv)

    try:
        with open(args.personas_json, encoding="utf-8") as fh:
            doc = json.load(fh)
    except (OSError, json.JSONDecodeError) as e:
        print(f"FAIL $: cannot read JSON: {e}")
        return 1
    with open(args.schema, encoding="utf-8") as fh:
        schema = json.load(fh)

    problems = validate(doc, schema)
    if problems:
        for p in problems:
            print(f"FAIL {p}")
        print(f"[validate_personas] {len(problems)} problem(s)")
        return 1
    n = len(doc.get("personas", []))
    print(f"[validate_personas] OK: {n} persona(s), {sum(len(p['search_behavior'][b]) for p in doc['personas'] for b in ('informational_queries','commercial_queries','transactional_queries','question_queries'))} sample queries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
