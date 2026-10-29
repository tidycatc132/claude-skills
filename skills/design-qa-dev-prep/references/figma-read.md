# Reading the templates from Figma

Load this when the user gives a Figma link and the Figma connector's tools are available. Their names carry the connector's server prefix (for example `mcp__Figma__get_metadata`); the reads used here are `get_metadata`, `get_variable_defs`, `get_design_context` and `get_screenshot`. If they are not available, say so in one line and fall back to `dqa.py template`.

1. **Open a session** if the connector asks for one (some versions need a session call with the file key before any read). The file key is the part after `/design/` in the link.
2. **Find the templates.** Read the file's metadata (pages and top-level frames). Match each frame to a page type in the briefs by its name ("Service Template", "Contact / Desktop"). Use the desktop frame when there are desktop and mobile versions. If a page type has no frame, leave it out of the inventory; the check reports it.
3. **List the containers.** For each template frame, read its direct children top to bottom. Each child is one line under `Sections:`. Map it to the brief section it holds by what it contains (its text layers and its name). Header, footer and navigation are `global`. A child that holds nothing in the brief (a testimonial strip the brief never asked for) is `none`. Record the layer name as Figma shows it.
4. **Count the room.** For the repeating question or content block, count how many instances the frame holds. When it is an auto-layout list or a component meant to repeat freely, write `no limit` only if the designer's notes or the component say so; otherwise write the count you see.
5. **CTAs.** Note which sections hold a button or a tap-to-call link.
6. **Colours and fonts.** Read the file's variables or styles for colours (hex) and text styles (family and weights). List only what the templates use.
7. **Assets.** For each image fill, note its frame name and the size of its container in pixels and the export format if set. Icons: the icon library named in the file or its components. Spacing: the spacing variables or the auto-layout gaps used most. Interactive elements: components with variants or prototype interactions (an FAQ item with open and closed states) and what they do.
8. Write the inventory with `Source: figma <link>` and today's date. Anything you could not read stays `<fill>`; never guess it.
