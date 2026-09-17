# The eval harness

**This is the real product.** Build it in week two, *before* writing serious remediation
code.

Two things are true at once and both matter:

1. It is the number that determines whether the business works — the automation pass
   rate drives the entire margin structure (see [`economics.md`](economics.md)).
2. It is separately the single most employable artifact in this project. It's rigorous,
   measurable, and in a domain where a federal agency just said the technology falls
   short. Most people claiming to be AI engineers cannot produce a number like this for
   their own system.

The same piece of work paying off twice.

## The ground truth set

Assemble **300–500 real government PDFs** spanning every type:

- Agendas
- Minutes
- Budgets with big tables
- Scanned resolutions from 1998
- Zoning maps
- Fillable permit forms
- Newsletters

Get **ground truth** for them: pay a professional remediator to properly fix a batch.

`[E]` That will cost a few thousand dollars and **it is the best money you will spend**,
because everything downstream depends on it.

> Sampling matters as much as size. The set has to match the *actual* document mix of
> the customers you intend to sell to, or the pass rate it reports is fiction. Stratify
> by document type and by complexity tier, and record the stratification.

## Metrics, measured on every change

| Metric | What it tells you |
|---|---|
| **veraPDF PDF/UA pass rate, by document type** | Structural conformance floor |
| **Tag tree agreement** vs. ground truth | Did you build the right structure |
| **Reading order correctness** | Does it make sense read aloud |
| **Alt text quality** — scored by a human on samples, by a judge model in bulk, *calibrated against the human scores* | The judgment layer, which is the whole thesis |
| **Human minutes to fix per page, after the pipeline runs** | ⬅ **the business metric** |

### The last one is the only business metric

**Human minutes to fix per page × loaded labor rate = your cost of goods sold.**

Track it **per document type** and you know exactly:
- what to **price**
- what to **refuse**
- what to **go fix in the pipeline next**

Everything else in the table is diagnostic. This one is the P&L.

## Rules

- **Run it on every change.** Model updates silently change outputs. Without this
  running continuously, you discover regressions when a customer does.
- **Calibrate the judge model against human scores** before trusting it in bulk, and
  re-calibrate when either the judge or the pipeline changes.
- **Report by document type, never in aggregate.** An 80% blended pass rate that's 95%
  on agendas and 30% on budgets is a completely different business from a uniform 80%.
- **No claim ships to a customer that isn't in the harness.** This is the liability
  posture as much as the engineering one — see [`risks.md`](risks.md).
- **veraPDF passing is necessary, not sufficient.** About half of Matterhorn's 136
  failure conditions require human eyes. A file can be PDF/UA-valid and useless.
