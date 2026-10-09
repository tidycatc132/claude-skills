# How `page_type` and `priority` are decided

`scripts/make_map.py` applies these rules in order; the first match wins.

1. **`location`**: the topic contains "near me", " in <place>", or a place suffix such as "city", "county", or a two-letter state code in capitals ("Ann Arbor MI").
2. **`blog`**: the topic starts with a question word (how, what, why, when, which, can, should, is, are) or contains "guide", "tips", "vs", or "checklist".
3. **`service`**: everything else.

`priority` follows the order of the seed file: the first third of the rows get `1`, the middle third `2`, the rest `3`. Ordering the seed file is therefore how the user expresses priority.

To override a classification, edit the single `page_type` cell in the CSV; allowed values are `service`, `location`, `blog`.
