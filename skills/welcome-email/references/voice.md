# WISE voice for client emails

The welcome email comes from the Account Manager at WISE, so it is written in WISE's voice. It is never written in the client's brand voice: the client's taglines, puns, slogans and exclamation-heavy style in the context file describe the client's marketing, not how WISE talks to them.

## How it sounds

- First person from the AM ("I'm Jordan, your Account Manager"), "we" for the WISE team.
- Plain, warm and confident. Short paragraphs of one to three sentences.
- Specific. Name one or two things from the context file that show we listened, in plain words: the goal they named, the service they most want to grow, the problem with today's site. Do not repeat the whole context back.
- Calm about effort: the form takes about 15 minutes, and anything they don't have handy can wait for the call.
- At most one exclamation mark in the whole email.

## What it never does

- Generic agency language. `check_email.py` fails these phrases: thrilled, excited to partner, excited to work, delighted, world-class, cutting-edge, best-in-class, don't hesitate, do not hesitate, synergy, game-changer.
- Facts the kickoff files don't hold: no results, rankings, traffic, review counts, prices or team sizes beyond what the context file says. Every number in the prose must appear in the kickoff files, except 1, 2, 3 and 15 (Week 1, 2 to 3 design options, a 15-minute form).
- Calendar promises. Say what happens and in what order; do not give dates unless the AM gave one.
- Ask for passwords. Access is by invitation (see `week-1-for-clients.md`).
- Links the AM did not give. No client website link, no social links, no made-up booking page.
