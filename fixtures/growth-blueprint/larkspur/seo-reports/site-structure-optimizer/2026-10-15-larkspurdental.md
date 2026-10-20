# Site structure: Larkspur Family Dental (architecture mode)

Mode: architecture. Site type: local service business (dental practice). New build, no existing site.

One-line finding: an 11-page service-led build fits inside the 12-page SOW with room for one later page.

## SOW page cap

SOW cap: 12 pages (kickoff/larkspur-dental/larkspur-dental-context.md, `SOW pages: 12`).

countable pages 11 / SOW cap 12

## Page decision table

| Page | Action | Score | Reason |
|---|---|---|---|
| Home | create | 10 | entry page |
| Emergency Dentist | create | 9.5 | P0 keyword, fastest-growing service |
| Family Dentistry | create | 9.0 | core patient base |
| Dental Implants | create | 9.0 | highest-value service |
| Sedation Dentistry | create | 8.0 | anxious-patient audience |
| Pediatric Dentistry | create | 7.5 | families with children |
| Invisalign | create | 7.0 | requested by the owner |
| Teeth Whitening | create | 6.5 | cosmetic add-on |
| Meridian Location | create | 7.0 | second service area |
| About | create | 8.0 | trust page |
| Our Team | create | 7.5 | three dentists |
| New Patients | create | 8.5 | conversion page |
| Contact | create | 8.0 | conversion page |

## URL map

| Page | URL | Parent | Nav location | Priority |
|---|---|---|---|---|
| Home | / | none | logo | high |
| Emergency Dentist | /emergency-dentist/ | / | header | high |
| Family Dentistry | /services/family-dentistry/ | /services/ | header | high |
| Dental Implants | /services/dental-implants/ | /services/ | header | high |
| Sedation Dentistry | /services/sedation-dentistry/ | /services/ | header | medium |
| Pediatric Dentistry | /services/pediatric-dentistry/ | /services/ | header | medium |
| Invisalign | /services/invisalign/ | /services/ | header | medium |
| Teeth Whitening | /services/teeth-whitening/ | /services/ | footer | low |
| Meridian Location | /meridian-dentist/ | / | footer | medium |
| About | /about/ | / | header | medium |
| Our Team | /about/team/ | /about/ | header | medium |
| New Patients | /new-patients/ | / | header | high |
| Contact | /contact/ | / | header CTA | high (not in SOW scope) |

## Score

Architecture score 95/100: start 100, -5 one parent with a single child (/about/). 

## Handoff

```yaml
status: DONE
objective: Site architecture for the Larkspur Family Dental new build
key_findings:
  - 11 countable pages inside the 12-page SOW cap
evidence:
  - keyword report 2026-10-14, SOW via the kickoff context
assumptions:
  - no existing site, so no redirects
open_loops:
  - none
recommended_next_skill: content-brief
```
