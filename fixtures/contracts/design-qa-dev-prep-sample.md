Client: Larchmont Electric · Checked: 2026-10-29 · Inventory: design/larchmont-electric/larchmont-electric-design-inventory.md (source: designer)

# Design QA and Dev Prep: Larchmont Electric

## Results

| Template | Check | Result | Detail |
|---|---|---|---|
| All | Inventory filled | PASS | designer |
| Service Pages | Template exists | PASS | Service Page / Desktop |
| Service Pages | Brief sections have containers | PASS | 5 of 5 |
| Service Pages | Containers have content | PASS | every container maps to a brief section |
| Service Pages | Section order | PASS | same order as the brief |
| Service Pages | Holds the longest page | PASS | no limit; longest is content/ev-charger-installation/article.md (8 H2 sections, 360 words) |
| Service Pages | CTA placement | PASS | Opening answer, Booking |
| Contact Page | Template exists | PASS | Contact / Desktop |
| Contact Page | Brief sections have containers | PASS | 5 of 5 |
| Contact Page | Containers have content | PASS | every container maps to a brief section |
| Contact Page | Section order | PASS | same order as the brief |
| Contact Page | Holds the longest page | PASS | holds 4; longest is content/contact/article.md (4 H2 sections, 44 words) |
| Contact Page | CTA placement | PASS | Contact Form, Phone and Email |
| All | Colours sourced | FLAG | not in the brand sources: #EEF2F6 |
| All | Fonts sourced | PASS | Barlow, Inter |
| All | Asset details complete | PASS | every asset has its details |

## To Fix

- Nothing to fix.

## To Confirm

1. All, Colours sourced: not in the brand sources: #EEF2F6. Design confirms.

## Mobile-First Priorities

### Service Pages

- On mobile the phone number and the Opening answer come first [article].
- Key Takeaways come before the question sections; the FAQ and Sources can come last [article].

### Contact Page

- On mobile the phone number comes before the form [article].

## Asset Checklist

### Images

- Service header photo (2): 1600 x 900, WebP
- Crew photo for the contact page: 1200 x 800, WebP
- Logo: larchmont-electric-logo.svg, navy and white versions, SVG

### Icon set

- Lucide, 2 px stroke

### Fonts

- Barlow 600, 700: Google Fonts
- Inter 400, 600: Google Fonts

### Colour palette

- #1B2A41: headings, header and footer
- #F2A900: buttons and the call strip
- #5B6770: body text
- #FFFFFF: page background
- #EEF2F6: background of the Takeaways List (not in the brand sources; Design confirms)

### Spacing

- 8 px base unit; 96 px between sections on desktop, 48 px on mobile

### Interactive elements

- FAQ List: each question opens and closes its answer; all closed on load
- Visit Request Form: name, phone, email, service needed, message; sends to office@larchmontelectric.com and shows a thank-you line
- Phone number in the Site Header: tap-to-call on mobile

RESULT: PASS
