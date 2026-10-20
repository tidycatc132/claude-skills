# Week 2 email: layout

The file has a header for the AM, a blank line, the `Subject:` line, a blank line, then the email itself from the greeting to the sign-off. Write it in this order.

```
Client: <client from facts>
To: <contact, exactly as the AM gave it>
Send date: <YYYY-MM-DD>
Reply by: <reply_by from facts>
Attach: <deck_file> (open first); <pdf_file> (reference copy)
Links: <each link the AM gave, joined with "; ", or "none">

Subject: <short, plain, names the Blueprint and the page content>

<greeting from facts>

<opening>

<recommendations>

<what is attached>

<what to look at and the three questions>

<reply-by and walkthrough>

<still owed>

<AM name>
Account Manager, WISE Digital Partners
```

With `--no-pdf` the `Attach:` line is only `<deck_file> (open first)`. The title line is `Account Manager, WISE Digital Partners` unless the AM gives another title (then pass `--title`).

## The parts

- **Greeting.** The `greeting` line from facts, on its own line (`Hi Jenna,` or `Hi Dr. Okafor,`).
- **Opening.** One or two sentences: the strategy and the page content for their site are ready.
- **Recommendations.** One lead-in sentence, then two or three `- ` bullets. Each restates one Key Strategic Bet in the client's terms: what we will do and why it matters to them, in one sentence. One bullet per bet; no two bullets from the same bet. A figure from the bet or the Executive Summary may carry a bullet. These are the only bullets apart from the still-owed lines.
- **What is attached.** Name `deck_file` and say it is the one to open first, in the same paragraph. Name `pdf_file` in the same or the next paragraph and call it the reference copy (for reading on a phone or forwarding). Give the deck link and the page copy link here if the AM gave them; otherwise say the page content is attached or will follow from the AM.
- **What to look at.** Ask them to focus on the overall direction, the proposed sitemap and the page content, not on fonts or wording polish. Then the three questions, word for word, each on its own line:
  `Does this feel right?`
  `Does anything surprise you?`
  `Is anything missing?`
- **Reply-by and walkthrough.** Ask for their thoughts by `reply_by_text` (for example "by Monday, October 26"), the only date in the email. Offer a short walkthrough call of the deck, with the booking link if the AM gave one.
- **Still owed.** One lead-in sentence, then every `asks` line from facts, pasted exactly, one per line. They name what the client still owes us: intake items, platform access we need their help with, and one line naming the pages whose copy has details marked for them. Leave the list out only when `asks` is empty.
- **Sign-off.** A short closing line, then the AM's name and the title line as the last two lines.

## Length

Under 250 words from the greeting to the title line, still-owed lines included. If it runs long, cut the opening, the lead-ins and the recommendation bullets to one short sentence each; keep every required part.
