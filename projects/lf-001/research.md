# Research — "Who Is Actually Paying for the AI Boom?"

**Status:** first pass. Every number below needs primary-source confirmation
before it goes in a script — see the confidence column. Secondary reporting is
fine for finding the story; it is not fine for stating a figure on screen.

---

## The question the video answers

AI companies are reporting enormous revenue and signing enormous contracts. A lot
of that money originates from the same companies receiving it. So: when Nvidia
reports chip sales, or Oracle reports a backlog, or Microsoft reports Azure
growth — **whose money is that, and where did it come from?**

Not "is this a bubble." That's unanswerable and every channel has already said
it. The answerable question is: *trace the money and see how many hands it
passes through.*

---

## The mechanism

The shape repeats across every deal:

1. An infrastructure company (chips or cloud) invests in, or guarantees debt for,
   an AI lab.
2. The lab spends that money with the infrastructure company.
3. The infrastructure company books it as revenue or backlog.

Nothing here is illegal or hidden — these are announced deals. The question is
what the revenue *means* when the customer's ability to pay was created by the
vendor.

This is vendor financing. It has a long history in telecoms and it has a known
failure mode: it works while demand grows, and it concentrates losses when demand
disappoints, because the vendor loses the sale *and* the investment.

---

## Claims and sources

| # | Claim | Source | Confidence |
|---|---|---|---|
| 1 | Oracle RPO reached **$638B**, up 363% YoY | [Oracle Q4 FY2026 release](https://investor.oracle.com/investor-news/news-details/2026/Oracle-Announces-Record-Q4-and-FY-2026-Results-Driven-by-Cloud-Infrastructure--Cloud-Applications/default.aspx), [SEC 8-K](https://www.sec.gov/Archives/edgar/data/0001341439/000119312526265848/orcl-ex99_1.htm) | **Primary — solid** |
| 2 | Prepaid + customer-supplied hardware in those AI contracts ≈ **$75B** | Same Oracle release | **Primary — solid** |
| 3 | Oracle–OpenAI **$300B / 5yr** cloud contract, starting 2027 | [DCD](https://www.datacenterdynamics.com/en/news/oracle-has-455bn-in-remaining-performance-obligations-at-end-of-q1-2026/), widely reported | Secondary — verify |
| 4 | Nvidia–OpenAI Sept 2025 LOI up to **$100B**, tied to 10GW | Widely reported | Secondary — verify |
| 5 | Feb 2026: that commitment collapsed; Nvidia took **$30B equity** in OpenAI's **$110B** round | [Benzinga timeline](https://www.benzinga.com/markets/tech/26/07/60713664/nvidia-funds-ai-frenzy-timeline-of-its-circular-financing-deals-so-far) | Secondary — verify |
| 6 | Nvidia in talks to backstop up to **$250B** of OpenAI datacentre leasing | [Axios](https://www.axios.com/2026/07/27/nvidia-openai-financing-ai-jensen-huang-ssi), [Al Jazeera](https://www.aljazeera.com/economy/2026/7/27/nvidia-plans-250bn-push-to-bolster-openais-infrastructure-ambitions) | Reported talks — **say "reportedly"** |
| 7 | Nvidia deals totalling ~**$750B** revived circular-financing concern | [Bloomberg](https://www.bloomberg.com/news/articles/2026-07-27/nvidia-s-750-billion-deals-revive-fear-of-ai-circular-financing) | Secondary — verify |
| 8 | Amazon put **$5B** more into Anthropic (total ~$13B); Anthropic pledged **$100B+** AWS spend over 10 years, up to 5GW | [TechCrunch](https://techcrunch.com/2026/04/20/anthropic-takes-5b-from-amazon-and-pledges-100b-in-cloud-spending-in-return/) | Secondary — verify |
| 9 | Microsoft + Nvidia invested ~**$15B** in Anthropic; Anthropic committed ~**$30B** Azure | [Tom's Hardware](https://www.tomshardware.com/tech-industry/artificial-intelligence/anthropic-signs-usd30-billion-deal-with-amazon-to-deploy-claude-on-aws-nvidia-and-microsoft-jointly-invest-usd15-billion-into-ai-firm-as-it-becomes-first-provider-across-azure-aws-and-google), [DCD](https://www.datacenterdynamics.com/en/news/anthropic-to-purchase-30bn-in-microsoft-azure-credits-nvidia-and-microsoft-to-invest-in-ai-company/) | Secondary — verify |
| 10 | OpenAI valued **$852B**; ~**$25B** annualised revenue mid-2026 | [Value Add VC](https://valueaddvc.com/blog/openai-valuation-2026-852-billion-after-the-122b-raise) | **Weak source — must verify** |
| 11 | Anthropic valued **$965B** after a $65B raise | [Al Jazeera](https://www.aljazeera.com/economy/2026/5/29/anthropic-soars-to-965bn-valuation-leapfrogging-openai), [Morningstar](https://www.morningstar.com/stocks/anthropic-bests-openai-valuation-race-hitting-965b) | Secondary — reasonable |
| 12 | OpenAI + Anthropic are **more than half** of a ~$2T cloud backlog across MSFT/ORCL/GOOG/AMZN | Single secondary source | **Weak — do not use unless confirmed** |

**The strongest single fact is #1 and #2**, because they're straight from Oracle's
own filing: a $638B backlog, of which $75B was prepaid or customer-supplied
hardware. That is Oracle telling you, in its own release, that a large chunk of
its record backlog was funded by the customer up front.

---

## The counter-argument, stated fairly

The industry's defence is not stupid and the video must give it properly:

- One side has capital and wants to sell compute; the other has revenue
  confidence but not billions in cash today. Vendor financing is how capital-
  intensive industries have always been built — railways, telecoms, aircraft.
- The contracts are announced and disclosed, not concealed.
- If the demand is real, this is simply the fastest route to building it.

The honest version of the argument is not "this is fraud." It's:
**these arrangements make the revenue harder to interpret, and they concentrate
risk in a smaller number of balance sheets than the headline numbers suggest.**

---

## The incentive lens (the Munger connection, used once)

Munger's point about incentives — that people respond to how they're measured,
not to what's true — applies without needing to name-drop him for a whole video.
When a vendor can create its own demand by financing the buyer, the incentive to
scrutinise that demand disappears on both sides.

**Use it as a lens near the end, not as the framing.** The reference video built
its entire structure around Munger; ours shouldn't, or we've made their video.

---

## Proposed argument structure (7 chapters, ~2 min each)

1. **The question** — the numbers are real; where did the money start?
2. **One deal, traced** — walk a single arrangement end to end. Concrete, not abstract.
3. **The pattern** — the same shape across Nvidia/OpenAI, Amazon/Anthropic, Microsoft/Anthropic.
4. **What the filings actually say** — Oracle's own numbers. This is the strongest chapter; lead the evidence with primary documents.
5. **Why smart people are doing this** — the counter-argument, given properly.
6. **The known failure mode** — vendor financing history, and what "circular" costs you when demand softens.
7. **What would actually tell us** — the specific indicators to watch. Ends on something useful rather than a prediction.

Chapter 7 is deliberately not a verdict. We don't know if it's a bubble, and
claiming to is how a channel gets caught out in eighteen months.

---

## Before scripting

- [ ] Confirm every figure marked "verify" against a primary source: SEC filings,
      company IR releases, official announcement posts.
- [ ] Drop or re-source claim #12 entirely.
- [ ] Get exact wording for anything attributed to a named person.
- [ ] For every claim, note the on-screen evidence: filing, chart, or clip.
- [ ] Decide the ~300 visuals against the chapter list, not afterwards.
