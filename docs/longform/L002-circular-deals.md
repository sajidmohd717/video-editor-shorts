# L002 — "How Circular Deals Are Driving the AI Boom" (Bloomberg Originals)

10:03 · 448k views · Jan 2026 · **same topic as lf-001**

> **Research and technique only. Never footage, never script.** Topics aren't
> ownable and a video on the same subject is legitimate; the writing is theirs.
> In this format the whole value is the thinking, and borrowed thinking has no
> edge over the original.

Torn down because lf-001's first cut was **90 clips drawn from 22 stock assets,
a mean reuse of 4.1×** — and the channel owner's verdict was blunt and correct:
*"all that it has is just b-roll stock video, which is extremely boring."*

---

## The finding: they have six visual registers, we had one

| Register | Example | lf-001 before |
|---|---|---|
| **Named-entity footage** | Nadella on stage as "Microsoft" is said; ORACLE building sign; NVIDIA campus sign | none |
| **Purpose-built motion graphics** | 47s node graph; abstract 3D renders | none |
| **Attributed interview** | talking head, lower third "Shirin Ghaffary / Reporter, Bloomberg News" | one silent 5.5s shot |
| **Sourced data charts** | "US Construction Spending… Source: Census Bureau" | one stat-chart |
| **Product surfaces** | Claude wordmark on paper, ChatGPT output on screen, macro | none |
| **Generic stock** | data-centre interiors | **~90% of the video** |

Generic stock is their *connective tissue*. It was our entire vocabulary.

---

## 1. Say a name, show that name (0:17–0:23, 0:46–0:56)

The clearest, cheapest, most repeatable thing in the video:

| narration | screen |
|---|---|
| "Microsoft" | Nadella on stage, Microsoft logo behind |
| "Meta" | Zuckerberg on stage, Meta blue |
| "Alphabet" | Google I/O stage, wide |
| "Oracle" | ORACLE building signage |
| "Nvidia" | NVIDIA campus sign |

Not one generic server rack among them. **A proper noun is a visual cue** —
naming a company and showing anonymous stock wastes the one moment where the
viewer is thinking about a specific company.

This is a near-perfect fit for our machinery: `plan_longform.py` already places
visuals by phrase, so "when the narration says NVIDIA, show NVIDIA" is a job
entry, not a feature.

---

## 2. A structure needs a diagram, not a montage (1:48–2:35)

**47 seconds** — 8% of the runtime — on one animated node graph: ~18 labelled
company spheres joined by curved edges, assembling progressively.

It earns that time because *"the money moves in a circle"* is a **structural
claim**, and no sequence of photographs can state a structure. This is F3 ("match
the visual to the shape of the claim") at the level of a whole argument rather
than a sentence.

Our shot list called for exactly this — "simple diagram: two boxes, arrows both
ways" — and it was never built, so the thesis was carried by circuit boards.

**Built as `entity-graph`, and deliberately different from theirs:** theirs is an
undirected network, which says *these companies are connected* — something every
viewer already assumes. Ours is **directed and labelled with amounts**, because
our claim is that money goes out and comes back. The outbound flows are accent
orange, the return flow white and equally strong: making the return arrow quieter
would undersell the only edge that matters.

Positions are authored, not force-solved — a physics layout settles differently
across Remotion's out-of-order workers.

---

## 3. Let the source speak, in a real block (2:39+)

A long, uninterrupted NYT interview clip with Anthropic's CEO — audio and all,
no narration over it.

We could not have done this before today: it requires cutting a hole in
continuous narration, which is now `sourceAudio` gap insertion (L14).

Also worth stealing: **every talking head carries a lower third with name and
outlet.** Attribution as a design element, not a caption.

---

## 4. Anchor audio as a montage (0:46–1:00)

Roughly 15 seconds where the narrator stops entirely and news anchors carry it.
This is the cold open we built and then dropped over Content ID exposure — the
technique is right, the sourcing is what has to change (L13).

---

## What to take

1. **Proper nouns get their own visuals.** Highest value per unit of work.
2. **Build the diagram the argument needs.** One good graphic beats a minute of texture.
3. **Attribute on screen** — name and outlet, every time.
4. **Charts cite a source** in the subtitle.
5. Product surfaces — logos, UI, documents — shot close.

## What not to take

- **Their script.** Ours is written from primary sources and reaches a different,
  more careful conclusion ("up to" is doing enormous work in these figures).
- **Their footage.** Broadcaster-owned, and the ident problem is L13.
- **The 18-node graph.** Impressive, borderline unreadable; four nodes and four
  labelled arrows carry our claim and can actually be followed at speed.
