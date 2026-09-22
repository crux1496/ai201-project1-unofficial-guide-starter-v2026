# The Unofficial Guide

Cruz Chigonda — corpus: `city_guides`

> **This file is your submission.** Fill it in as you go — most sections get
> written during the milestone that produces them, not at the end.
>
> How the starter works, and every command you'll need, is in `RUNNING.md`.
> Leave that file alone.
>
> **Paste everything as text.** No screenshots, no video. A typed table gets
> full credit; a picture of the same table gets none.
>
> Delete these instruction blocks as you replace them. The `<!-- -->` comments
> are notes to you and don't show up when the page renders — you can leave them
> or remove them.

---

# Unit 1

## What This Does

A retrieval-augmented generation pipeline over `city_guides`, a corpus of 14
travel guides to a fictional region: ten town guides plus four cross-cutting
guides covering regional transport, eating, walking routes and accessibility.
The corpus is roughly 29.5 KB of markdown, which segments into 96 chunks
indexed in Chroma under `all-MiniLM-L6-v2` embeddings with cosine distance.

A query is embedded into the same space, the k=5 nearest chunks are retrieved,
and those chunks are passed to `gemini-3.5-flash-lite` as the sole permitted
evidence for its answer. The target queries are factual and locally scoped —
tram headways in Marchwood, the tidal mechanism that floods the Elder Ness
approach road, pub serving hours in Kestrelford — the class of question where a
correct answer exists in exactly one section of one document.

The system is constrained to fail closed. A distance threshold is applied to
the best retrieved chunk before generation, so out-of-corpus queries are
rejected deterministically rather than being passed to the model and relying on
it to decline. This trades recall for precision, which is the correct trade
when an unsupported answer is more costly than a refusal.

## Chunking Strategy

**Chunk size:** 800 characters, but as a ceiling rather than a target
**Overlap:** none — replaced by a repeated title and heading on every chunk

The governing observation from Milestone 1 is that this corpus carries explicit
structural markup that already encodes its semantic boundaries. Every guide is
partitioned under `##` headings — Getting there, Getting around, Eat and drink,
Where to stay — and each section is topically self-contained. The distribution
is tight: the largest document is 2,547 characters and the largest single
section is roughly 600. Fixed-width windowing over this corpus therefore
imposes an arbitrary partition on text that already has a principled one, and
splits sections mid-argument at offsets that carry no meaning.

The implemented strategy segments on heading and paragraph boundaries, treating
800 characters as a packing ceiling rather than a target width. Since no
section approaches that bound, the character limit is never reached in practice
and the mapping is effectively one chunk per `##` section. The limit remains as
a guard for corpora with different length characteristics; when it does fire,
the split is taken at a sentence boundary, so no chunk terminates mid-sentence.

Overlap was eliminated rather than tuned. Its purpose is to prevent an answer
spanning a boundary from being lost to both neighbours, but that failure mode
presupposes boundaries placed without regard to content. Once boundaries
coincide with section breaks, the residual risk is different: a retrieved chunk
loses the context that identifies its subject. "## Where to stay" is
semantically near-identical across all ten town guides in isolation. The
mitigation is a propagated header — every chunk after a document's first is
prefixed with the document title and its section heading — which restores
identifying context at roughly 30 characters of overhead against the 120 the
overlap consumed.

**One revision during implementation.** The boundary detector initially matched
only markdown `##`. This is sound for `city_guides` but degrades silently on
plain-text corpora: validating against `practice`, I found chunks terminating
on an orphaned heading line ("Making the game shorter") with its body deferred
to the following chunk. The predicate was generalised to admit short unpunctuated
single-line paragraphs as headings, which recovers the intended segmentation
without special-casing a corpus.

## Sample Chunks

**Chunk 1** — source: `guide_accessibility.md#0` — produced by: `chunker.py::split_documents`

```
# Getting around the region with limited mobility

An honest assessment rather than a promotional one. Some of these places are
difficult and it is better to know in advance.
```

**Chunk 2** — source: `guide_corry_vale.md#5` — produced by: `chunker.py::split_documents`

```
# Corry Vale

## Where to stay

Perhaps thirty beds in the entire valley, spread across two pubs and a handful of farmhouse rooms. In summer these are booked months ahead. Camping is permitted on two marked fields and nowhere else.
```

**Chunk 3** — source: `guide_givens_mill.md#2` — produced by: `chunker.py::split_documents`

```
# Givens Mill

## Getting around

Everything is on one street along the river. The mill is at one end and the church at the other, eight minutes apart. The riverside path continues in both directions for as far as you want to walk.
```

**Chunk 4** — source: `guide_kestrelford.md#5` — produced by: `chunker.py::split_documents`

```
# Kestrelford

## Where to stay

Two inns on the square and a handful of rooms above the pubs. Booking ahead matters between May and September and not at all otherwise. There is no accommodation of any kind within four miles of the town in either direction.
```

**Chunk 5** — source: `guide_regional_transport.md#0` — produced by: `chunker.py::split_documents`

```
# Getting around the region

## The railway

The line runs along the river valley, connecting Brightwater to the regional
hub in 50 minutes. Eleven services a day on weekdays, six on Sundays. The line
north of Brightwater closed in 1963 and everything beyond it is bus or car.

Tickets are cheaper booked the day before than on the day, and considerably
cheaper than that booked a week ahead. There is no ticket office at
Brightwater station outside weekday mornings; the machine on the platform takes
cards only.
```

## Sample Answer

<!-- One complete question and answer, pasted as text, with the source line
     visible. Milestone 4. -->

**Question:** How often do the trams run in Marchwood?

**Answer:**

```
  (best distance 0.244, cutoff 0.6)

In Marchwood, the tram network runs every 8 minutes on weekdays and every 15
minutes at weekends (source: `guide_marchwood.md`).

Sources retrieved: guide_accessibility.md, guide_eating.md, guide_marchwood.md
```

**My relevance cutoff:** 0.6, retained rather than retuned. The two classes are
linearly separable by a wide margin in this metric: in-corpus best distances
occupy [0.244, 0.419] and out-of-corpus best distances occupy [0.803, 0.975],
leaving a 0.384-wide interval containing no observation. Any threshold in
roughly [0.45, 0.80] yields identical classifications on this sample, so the
decision is underdetermined by the data and 0.6 is chosen as an interior point
that maximises margin to both classes.

The separation is almost certainly optimistic. The negative class is drawn from
semantically distant domains — internal combustion, association football, Rust
syntax — and so samples the tail rather than the boundary. The adversarial case
is a near-miss: a query about a town in the same region that the guides simply
omit, which would share vocabulary and register with the corpus while having no
supporting passage. That case is untested here and is where I would expect the
threshold to be doing real work rather than separating the obvious.

<!-- The number you set in config.py, and how you got there.

     You ran five questions your corpus covers and the five in OUT_OF_SCOPE
     that it clearly doesn't, and wrote down the best distance for each. What
     did those two groups look like? Where was the gap? Put the actual numbers
     here — the table below wants all ten rows.

     Milestone 4. -->

| Question | In corpus? | Best distance |
|---|---|---|
| How often do the trams run in Marchwood? | yes | 0.244 |
| Why does the road to Elder Ness flood? | yes | 0.346 |
| Can I eat late in the evening in Kestrelford? | yes | 0.368 |
| How do I get to Kestrelford on a Sunday? | yes | 0.370 |
| Which towns are easiest with limited mobility? | yes | 0.419 |
| What is the capital of Mongolia? | no | 0.803 |
| What is the recommended dosage of ibuprofen for a headache? | no | 0.835 |
| How do I write a for loop in Rust? | no | 0.837 |
| How do I change the oil in a diesel engine? | no | 0.888 |
| Who won the 1994 World Cup? | no | 0.975 |

## How I Used AI

<!-- Two specific moments. For each: what you asked for, what came back, and
     what you changed about it.

     "I asked Claude to write the chunking function from my notes. It ignored
     the overlap, so I added that myself" is the level of detail we're after.
     "I used AI to help me code" is not.

     Milestone 5. -->

**1. Replacing the chunker.** I asked Claude to rewrite `split_documents`,
telling it my documents were guides split under markdown headings. The approach
was right — pack paragraphs, break at every heading — but I printed the chunks
instead of just reading the diff, and two bugs turned up. Some chunks were
nothing but a heading, 23 characters of "## Straightforward" with no text under
it. And the chunk after a heading had dropped the heading, so half a section
didn't say what section it was. Same cause: it flushed the buffer on hitting a
heading without checking if anything was in it yet.

I then ran it over `practice`, a corpus it hadn't been written for, and it
failed there too — plain headings with no `##` weren't detected. That's the fix
under Chunking Strategy. None of the three bugs were visible in the code and
all three were obvious in the output, which is the check that matters here.

**2. Writing criteria 4 and 5.** I asked Claude to draft the two criteria I had
to invent, then told it to cut them down. The useful part was a number it got
wrong: it wrote that chunk count should equal document count "(92)" when
`campus_life` has 88. It caught that when it went to check. The only thing
criterion 4 has going for it is that I can check it, so a wrong number makes it
fail for a reason that says nothing about my pipeline.

The same check found something I'd missed. `config.py`, `questions.py` and my
Milestone 3 output each pointed at a different corpus, which meant my five test
questions were written for a corpus I'd stopped using — and I'd have submitted
them that way.

<!-- ── Stretch features ─────────────────────────────────────────────────────
     Doing one? Say so here BEFORE you start. A feature this README never
     claims earns nothing.
     ───────────────────────────────────────────────────────────────────────── -->

---

# Unit 2

<!-- These sections get ADDED to what's already above. Don't delete or rewrite
     unit 1 — the point is that someone can see what you said before you knew
     how it went. -->

## Run Log — Before

<!-- Your five criteria, three runs each. `python run_eval.py --label before`
     runs the questions, puts the OUT_OF_SCOPE ones through the gate, and
     writes it all into results/ for you. Targets come from criteria.md; the
     verdict column is your call.

     Criterion 3 is measured in one deterministic pass rather than three, so
     the same number goes in all three run columns. That's correct, not lazy.

     Milestone 1. -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 |  |  |  |  |
| 2. Every answer names a source | 5 of 5 |  |  |  |  |
| 3. Gate stops out-of-corpus questions | 4 of 5 |  |  |  |  |
| 4. | | | | | |
| 5. | | | | | |

<!-- Underneath, paste the REAL output for each criterion from one of your
     runs — the actual text your system produced, not a description of it.
     Name the file and function that produced it. -->

## Verdicts

<!-- MET or MISSED for each of the five, against the target you wrote last
     unit — not a new one. Plus a sentence on how you decided. That sentence
     matters most where it was close.

     If your target said 4 of 5 and your runs came out 4, 3, 4, that's a MISS.
     The target has to hold, not show up occasionally.

     Milestone 2. -->

| # | Criterion | Verdict | How I decided |
|---|---|---|---|
| 1 |  |  |  |
| 2 |  |  |  |
| 3 |  |  |  |
| 4 |  |  |  |
| 5 |  |  |  |

## Diagnoses

<!-- For each miss: which stage caused it, and how. The stage alone isn't
     enough — you need the mechanism.

     Not a diagnosis: "Question 3 didn't work."
     A diagnosis:     "Question 3 asks about laundry costs. The answer is in
                       one sentence that got split across two chunks, so
                       neither chunk on its own contains it."

     The five stages: loading → chunking → embedding → retrieval → generation.

     Look for a pattern. If three misses all ask about numbers, that's one
     problem, not three.

     Missed nothing? Say so, then say honestly whether your targets were set
     low, and which one you'd tighten and to what.

     Milestone 3. -->

## The Improvement

**What I changed:**

**Why I picked it:**

<!-- Connect it to a specific diagnosis above in one sentence. If you can't,
     you picked a fix because it sounded impressive. -->

### Run Log — After

<!-- Same format, same five criteria, three runs each.
     `python run_eval.py --label after` -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 |  |  |  |  |
| 2. Every answer names a source | 5 of 5 |  |  |  |  |
| 3. Gate stops out-of-corpus questions | 4 of 5 |  |  |  |  |
| 4. | | | | | |
| 5. | | | | | |

**Did it help?**

<!-- Say plainly whether it did, and how you know. If it made things worse,
     say that — a change that backfired, honestly reported, earns full credit
     and is more interesting than one that worked. What matters is that you can
     tell.

     Milestone 4. -->

## What's Still Broken

<!-- For each criterion still missed after your fix: what you'd do about it,
     and why you stopped where you did.

     "I ran out of time" is fine if it's true. Pretending nothing is left is
     not.

     Milestone 5. -->

## What I'd Do Differently

<!-- Knowing what you know now — which of your five criteria would you write
     differently, and why?

     Milestone 5. -->
