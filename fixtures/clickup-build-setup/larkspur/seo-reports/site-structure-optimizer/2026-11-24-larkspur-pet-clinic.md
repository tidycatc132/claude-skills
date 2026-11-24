# Site structure: Larkspur Pet Clinic (architecture mode)

Mode: architecture. Site type: local service business.

## URL map

| Page | URL | Parent | Nav location | Priority |
|---|---|---|---|---|
| Home | / | - | logo | P1 |
| Services | /services | Home | main | P1 |
| Dental Care | /services/dental-care | Services | main dropdown | P1 |
| Vaccinations | /services/vaccinations | Services | main dropdown | P2 |
| About | /about | Home | main | P2 |
| Contact | /contact | Home | main, footer | P1 |
| Privacy Policy | /privacy-policy | Home | footer | P3 |

## Redirect map

| Old URL | New URL | Note |
|---|---|---|
| /dental | /services/dental-care | 301 |
