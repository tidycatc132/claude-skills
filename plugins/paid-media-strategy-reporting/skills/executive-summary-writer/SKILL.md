---
name: executive-summary-writer
description: Write a concise executive summary of paid media performance or strategy for a client executive or agency leadership, leading with the business outcome, the one or two reasons behind it, the decisions needed, and the risk, in under one page and in plain language, from a report, data, or notes. Use whenever the user asks for an executive summary, a TL;DR of the report, a short update for the CEO or owner, talking points for a client call, a leadership email, or how to explain results to a non-marketer, even if they only say can you boil this down.
---

# Executive Summary Writer

Executives read the first paragraph and decide whether to read the rest. They care about money in, business out, what changed, and what they need to decide. This skill compresses a report into that, without losing honesty.

## Principle: outcome first, plain words, one ask
Open with the result in business terms (leads, revenue, cost per customer), say whether it met the goal, give the reason in a sentence, and end with the decision or approval needed. Cut metrics that do not change a decision.

## Inputs
- The full report, dataset, or notes to summarize
- The audience: client owner, marketing director, agency leadership, and what they already know
- Goals and thresholds from `clients/<slug>/context.md`
- Any decisions pending

## Process
1. **Identify the audience and the decision.** What does this reader need to know and do after reading?
2. **Find the headline** in the source: the outcome versus goal. Verify the figures against the source data; do not repeat a number you cannot trace.
3. **Choose three supporting points at most:** the main driver, the biggest risk or problem, and the best opportunity. Each gets one or two sentences with one number.
4. **Replace jargon** with business language (say "cost per lead" not "CPA", and explain any necessary term in a clause).
5. **Be honest about bad news:** state it early and pair it with the plan. Do not soften a miss into vague language or inflate a modest win.
6. **End with the ask:** the specific decisions, approvals, or inputs needed and by when.
7. **Check length and facts:** under 200 words for the body unless asked otherwise; recheck every number against the source.

## Output
Return the summary in the conversation, formatted for pasting into an email or the top of a report. Save to `clients/<slug>/outputs/YYYY-MM/exec-summary.md` when it accompanies a report.
```
Subject line (if email).
Headline sentence.
Three supporting points.
What we are doing next.
Decisions needed, with dates.
```
Offer a talking-points version (five bullets) for calls on request.

## Rules
- No fabricated numbers or causes; if the source does not explain a movement, say it is under review.
- No metric appears without its comparison (goal or prior period).
- Do not use hype or hedging fog; state plainly what is known and unknown.
- Keep the tone appropriate to the relationship, direct and respectful.
