# Source clips — lf-001 "Who Is Actually Paying for the AI Boom?"

Supplied by the channel owner. Identified and assessed below.

| ID | Title | Channel | Len | Views | Date |
|---|---|---|---|---|---|
| `9yy_Wz0BbyU` | How Circular Deals Are Driving the AI Boom | **Bloomberg Originals** | 10:00 | 448k | 2026-01-23 |
| `Q0TpWitfxPk` | The State of the AI Industry is Freaking Me Out | **Hank Green** | 16:30 | 3.69M | 2025-10-16 |
| `o-utsp4194g` | AI boom transforming the venture capital, megacap investing landscape | **CNBC Television** | 1:30 | 2.7k | 2025-12-08 |
| `705SXlptCCY` | Will the AI bubble burst or boom? | **Al Jazeera (The Stream)** | — | 1.5k | — |

---

## Assessment — read before using

### The two "authoritative figures" are not the same kind of source

**CNBC and Al Jazeera** are broadcast news. Short excerpts as evidence for a
claim our narration makes is the standard commentary position (see
`pipeline/newsclip.py` docstring). Fine, in short excerpts, with the chyron
visible — the chyron is part of what makes it evidence.

**Bloomberg Originals and Hank Green are a different problem.** Both are
*already the same kind of video we are making*: a produced explainer, on our
exact topic, carrying an argument. Cutting from them is not using evidence — it
is using someone else's conclusions, and the Bloomberg piece in particular
covers the identical subject.

**Rule for this video:** treat Bloomberg and Hank Green as **research, not
footage.** Watch them, note which primary sources they cite, then go get those
primary sources ourselves. If a point of theirs is worth making, make it from the
document they got it from.

Two reasons, and the second matters more:

1. Lifting from a produced explainer on the same topic is the closest thing to
   remaking their video, which is the one outcome guaranteed to be worse than the
   original (L-log, "on making versions of studied videos").
2. Bloomberg Originals is a commercial licensor of its own footage and enforces
   accordingly.

### What we should be cutting from instead

For this topic the strongest footage is **primary**, and most of it is freely
usable or a much safer position:

- **Earnings calls** — Oracle, Nvidia, Microsoft. Companies post these; the
  speaker is the CEO stating the number themselves.
- **Investor-day and keynote footage** — Nvidia GTC, Microsoft Build, AWS
  re:Invent. Posted by the companies.
- **Congressional hearings** — C-SPAN. Frequently public domain.
- **The filings themselves** — SEC 8-K/10-Q pages, screenshotted with the line
  highlighted. This is the single most repeatable device in L001 and it costs
  nothing but a browser.
- **Conference interviews** the outlets post in full.

Per L001's inventory, ~55% of that reference is footage of the actual people —
but the bulk of it is press conferences, hearings and interviews, **not**
other people's explainers.

---

## Next actions

- [ ] Watch Bloomberg + Hank Green **for their sourcing**, list the primary
      documents they cite, and pull those.
- [ ] Pull CNBC / Al Jazeera excerpts only where they evidence a specific claim,
      a few seconds each, chyron visible.
- [ ] Screenshot the Oracle 8-K and Q4 release with the RPO and prepaid-hardware
      lines highlighted — this is our strongest single piece of evidence.
- [ ] Find earnings-call footage for the same statements.
