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

## VERIFIED against primary sources (2026-08-08)

### Oracle — confirmed, use freely
From Oracle's own Q4 FY2026 release (10 June 2026):

- RPO **$638B**, up **363%** YoY
- Sequentially **+$85B** from Q3's **$553B**
- **"The prepaid and customer supplied hardware portions of our large AI
  contracts now total $75 billion."** — Oracle's own words
- Q4 cloud revenue **$9.9B** (+47%); FY2026 cloud revenue **$34.0B** (+39%)

Note: the release attributes none of this to a named executive, so **do not put
words in a CEO's mouth on screen.** Attribute to "Oracle's Q4 release".

### Anthropic / Microsoft / NVIDIA — secondary reporting was WRONG

Secondary coverage said *"Microsoft and Nvidia invested roughly $15 billion at a
$350 billion valuation."* [Anthropic's own announcement](https://www.anthropic.com/news/microsoft-nvidia-anthropic-announce-strategic-partnerships)
says something materially different:

- NVIDIA committing to invest **up to $10B**; Microsoft **up to $5B** — separate
  commitments, and **"up to"**, not money already invested
- Anthropic committing to purchase **$30B of Azure compute**, plus contracting
  additional capacity up to **1 gigawatt**

"Up to $15B committed" and "$15B invested" are not the same claim. **This is
exactly the error the video is about** — and making it ourselves would be fatal.

### Anthropic valuation — confirmed
- Series H: **$65B raised at $965B post-money** ([Anthropic](https://www.anthropic.com/news/series-h))
- Earlier Series G: **$30B at $380B post-money** ([Anthropic](https://www.anthropic.com/news/anthropic-raises-30-billion-series-g-funding-380-billion-post-money-valuation))

That's a **$585B valuation increase between two rounds** — worth a beat of its own.

### Anthropic / Amazon — confirmed direction
[Anthropic's announcement](https://www.anthropic.com/news/anthropic-amazon-compute)
covers expanded collaboration for **up to 5 GW** of new compute. Confirm the
dollar figures against the same page before use.

### NVIDIA / OpenAI — confirmed, and it completes the pattern
From [OpenAI's own announcement](https://openai.com/index/openai-nvidia-systems-partnership/)
and [NVIDIA's newsroom](https://nvidianews.nvidia.com/news/openai-and-nvidia-announce-strategic-partnership-to-deploy-10gw-of-nvidia-systems),
22 September 2025:

- A **letter of intent** — not a signed, binding deal
- At least **10 gigawatts** of NVIDIA systems
- NVIDIA **"intends to invest up to $100 billion"**, released **progressively as
  each gigawatt is deployed**
- First gigawatt in **H2 2026** on the Vera Rubin platform

Read the qualifiers: *letter of intent*, *intends to*, *up to*, *progressively as
deployed*. It was reported, and priced, as a $100B investment.

### Still unverified — do not script yet
- The Feb 2026 collapse of the $100B commitment and the $30B equity stake that
  replaced it (#5). **If true this is the single best fact in the video** — the
  headline number never arrived. Needs a primary source.
- Nvidia's reported $250B backstop and $350B chip financing (#6, #7). **Reported
  talks.** Either word them "reportedly" or cut them.
- OpenAI valuation and revenue (#10) — weak source.
- **Claim #12 is dropped.**

---

## THE THESIS, now that three primary sources agree

The video does not need to allege anything. It only needs to read the
announcements carefully, because they say it themselves:

| Deal | Headline | What the announcement actually says |
|---|---|---|
| NVIDIA → OpenAI | "$100B investment" | *Letter of intent.* "Intends to invest **up to** $100B", released progressively per gigawatt deployed |
| NVIDIA + Microsoft → Anthropic | "$15B invested" | **Up to** $10B and **up to** $5B — separate commitments, against a $30B Azure purchase |
| Oracle | "$638B backlog" | RPO — contracted future obligations, **not revenue**; $75B of it prepaid or customer-supplied hardware |

**The answer to "who is actually paying" is: in many cases, less money has moved
than the headlines imply — and where it has moved, it frequently moved in a
circle.**

That's a defensible, checkable claim built entirely from companies' own words. It
requires no accusation, no prediction, and no insider knowledge — which is
exactly what makes it strong.

### Method note
Two of the first four things checked were wrong or overstated in secondary
reporting. **Every figure gets a primary source or it doesn't go on screen.**
For a video whose subject is misleading numbers, this isn't diligence — it's the
whole credibility of the piece.

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
