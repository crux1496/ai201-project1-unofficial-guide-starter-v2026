# Acceptance criteria — The Unofficial Guide

Five criteria that say what "working" means for this system, written in unit 1
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"Retrieval works"* is an opinion. *"For at
least 4 of my 5 test questions, the top results include a chunk containing the
answer"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter or looser one. A reason that says something about your corpus or your
pipeline earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

---

## 1. Retrieved chunks contain the answer

For at least 4 of my 5 test questions, the retrieved chunks include one that
contains the answer.

**Why this target:**
Four rather than five because one of my five queries is structurally hard for a
bi-encoder. "How do I get to Kestrelford on a Sunday?" competes against three
sections of the same document that discuss Saturday markets and opening days,
which carry higher lexical overlap with the query than the transport section
that actually answers it. I expect that one to miss at k=5 and the remaining
four to hit, and I would rather state that in advance than discover it and
rationalise it afterwards.

---

## 2. Every answer names a source

Every answer the system produces names at least one source document.

**Why this target:**
All five, because this is the one criterion whose satisfaction is enforced
rather than hoped for. Attribution is demanded explicitly by the system
instruction, every chunk is injected under a `[from <filename>]` header, and a
query that retrieves nothing close enough is refused before generation — so
there is no path to an answer that lacks a candidate source. A miss here would
mean the model disregarded a direct instruction while the evidence was in front
of it, which is a defect rather than an acceptable rate.

---

## 3. The relevance gate stops out-of-corpus questions

When I ask a question my documents clearly don't cover, the relevance gate
stops it and the system returns "I don't have enough information about that" —
in at least 4 of 5 tries.

<!-- The five questions are the ones in `OUT_OF_SCOPE` at the bottom of
     `questions.py`, and `run_eval.py` puts them through the gate and writes
     what happened into your run log. Swap them for your own if you'd rather —
     just keep five of them, or the "4 of 5" above has nothing to be 4 of. -->

**Why this target:**
The two classes separate cleanly under cosine distance: in-corpus queries
occupy [0.244, 0.419] and out-of-corpus queries [0.803, 0.975], with a
0.384-wide empty interval between them and a threshold of 0.6 sitting in its
interior. Under that margin the gate should reject all five, so 4 of 5 is
deliberately slack — the negatives I am testing with are drawn from unrelated
domains and sample the easy tail of the distribution. I am holding a margin for
the case I have not tested, a query about the same region that the guides
happen not to cover, which would sit far closer to the boundary.

---

## 4. Chunks are self-contained at section granularity

No chunk terminates mid-sentence, and every chunk carries the document title
that identifies its subject — both holding for 96 of 96 chunks in the index.

**Why this target:**
The corpus is pre-partitioned under `##` headings into topically independent
sections, so a chunk that ends mid-sentence indicates the splitter overriding a
boundary the document already supplied. The second clause matters more than the
first: the ten town guides share a near-identical section schema, so a chunk
consisting of "## Where to stay" plus a paragraph is ambiguous across ten
documents unless the title propagates into it. A count of 96 rather than a
proportion is defensible here because both properties are structural
consequences of the algorithm, not statistical tendencies — a single violation
is a defect, not noise.

---

## 5. Source attribution is correct, not merely present

For at least 4 of my 5 test questions, the cited source is the document that
actually contains the answer.

**Why this target:**
Criterion 2 is satisfied by any filename, and this corpus makes a wrong one
cheap: every town guide carries the same section headings, so a "## Getting
there" chunk from the wrong town is lexically plausible and superficially
responsive. The bound is 4 rather than 5 because retrieval already fails on one
of my five questions — the Kestrelford Sunday-transport query places its
answering chunk at rank 10 — and an answer assembled from the wrong section
cannot be expected to cite the right one.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 2 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 1. Retrieved chunks contain the answer

         For at least 4 of my 5 test questions, the retrieved chunks include
         one that contains the answer.

         **Why this target:** ...

         > **Revised in unit 2:** For at least 4 of 5 questions, the top three
         > results contain the answer.
         >
         > **Why revised:** I couldn't judge "the chunks include one that
         > contains the answer" the same way twice — I scored two questions
         > differently on Monday than on Wednesday. The new version is
         > something I can actually check.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said 4 of 5 but got 2 of 5, so 2 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.

     The whole reason the originals stay visible is so someone can see what you
     said before you knew the answer.
     ───────────────────────────────────────────────────────────────────────── -->
