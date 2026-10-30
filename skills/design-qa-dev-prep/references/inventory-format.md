# Design inventory format

`design/<slug>/<slug>-design-inventory.md`. One file per client. The designer fills it by hand, or you write it from Figma. `dqa.py template` writes a blank one with every template and brief section already listed. The script reads the lines below exactly, so keep the labels as shown.

## Header

```
Client: <client name>
Source: designer                       or    Source: figma <Figma file link>
Filled: <YYYY-MM-DD>

# Design Inventory: <client name>
```

## One block per template

The heading names the page type exactly as the page-type design briefs do (`Service Pages`, `Location Pages`, `About Page`, `Contact Page`, `Resource Pages`).

```
## Template: Service Pages

Frame: <the frame or page name in Figma>
Holds H2 sections: <a number, or no limit>
Sections:
- <layer name> -> <brief section>
- <layer name> -> global
- <layer name> -> none
CTAs after: <brief section>, <brief section>
```

- `Sections:` lists the template's containers top to bottom, one per line, as `<layer name> -> <brief section>`. The brief section is a name from that page type's Content Map, written as the brief writes it. `global` is header, footer or navigation. `none` is a container that holds no section in the brief (it fails `Containers have content`).
- `Holds H2 sections:` is how many question or content sections the template holds before it runs out of room. A repeating block with no limit is `no limit`. The script compares it with the longest page of the type.
- `CTAs after:` names the brief sections that carry a call to action, comma separated.

## Site-wide lists

One bullet per item, label first, a colon, then the detail.

```
## Colours
- #1B2A41: where it is used

## Fonts
- Barlow 600, 700: Google Fonts        (family and weights, then where the files come from)

## Images
- Hero photo: 1920 x 1080, WebP        (width x height and format; an SVG needs no size)

## Icon Set
- Lucide, 2 px stroke

## Spacing
- 8 px base unit; 96 px between sections on desktop

## Interactive Elements
- FAQ List: each question opens and closes its answer   (what it does)
```

Any line still holding `<fill>` fails `Inventory filled`.
