# adascan

Automated ADA Title II accessibility scanning and PDF remediation for US local government.

This repo starts as a **thesis and design document**, not code. Everything here is
written down so it can be argued with, revised, and eventually replaced by working
software. The single most important discipline: **keep grounded facts and estimates
visibly separate.** Every doc in `docs/` marks which is which.

## The one-paragraph version

DOJ's ADA Title II web accessibility rule requires WCAG 2.1 Level AA and has been
pushed to **April 26, 2027** (entities serving 50,000+) and **April 26, 2028**
(everyone smaller, plus every special district regardless of size). There are
**90,837 local governments** in the US and essentially none are ready. When DOJ
explained the extension, one stated reason was the **limits of generative AI for
remediation** — a federal agency documenting a capability gap in the thing it is
legally mandating on a fixed date. Manual PDF remediation sells for **$5–$25/page**.
A pipeline's marginal cost is cents. That gap is the business.

Colorado is the starting market: **HB21-1110** already binds state and local entities,
its deadline has already passed, and it carries a **$3,500-per-violation** penalty
payable directly to plaintiffs. Colorado governments are exposed *now*, not in 2027.

## Build order (deliberately not the obvious one)

Four separable systems. Most people would build them 2 → 1 → 4 → 3. That order kills you.

| # | System | Purpose | Order |
|---|--------|---------|-------|
| 1 | **Scanner** | Crawl a gov domain, inventory pages + PDFs, test WCAG 2.1 AA, generate an audit report | **First** — it's the sales tool |
| 3 | **Eval harness** | Measure honestly what fraction of real gov documents the pipeline fixes correctly | **Second** — it's the actual product |
| 2 | **Remediation pipeline** | Tag, structure, and validate PDFs | Third |
| 4 | **Review tool** | Human handles what the pipeline can't | Fourth |

The scanner ships before the pipeline because a free audit with a specific number
about a specific entity *is* the sales motion. The eval harness comes before the
pipeline because the pipeline's automation pass rate is the only variable that
decides whether this is an 80%-margin software business or a staffing agency.

## Docs

- [`docs/opportunity.md`](docs/opportunity.md) — the regulatory setup, market size, why Colorado
- [`docs/economics.md`](docs/economics.md) — unit economics, customer values, scenarios, the four real drivers
- [`docs/architecture.md`](docs/architecture.md) — stages 0–6, the stack, where AI goes and where it must not
- [`docs/eval-harness.md`](docs/eval-harness.md) — the ground truth set and the metrics that matter
- [`docs/human-in-the-loop.md`](docs/human-in-the-loop.md) — reviewers, screen reader QA, sign-off, liability posture
- [`docs/risks.md`](docs/risks.md) — honest risks, including the one that matters most
- [`docs/roadmap.md`](docs/roadmap.md) — the 30-day test
- [`docs/open-questions.md`](docs/open-questions.md) — what has to be answered before scaling anything
- [`docs/sources.md`](docs/sources.md) — every claim, and whether it's been verified in-repo
- [`TODO.md`](TODO.md) — running state: done / in progress / next

## Ground rules baked into this project

1. **Do not promise full automation.** DOJ's stated reason for the delay is the
   warning label. Complex tables, scanned forms, maps and multi-column layouts still
   need a person. Price a hybrid and be explicit about what gets human review.
2. **Do real remediation. Never overlay widgets.** Overlay vendors have a deservedly
   bad reputation and get sued over it.
3. **A human signs off on every delivered batch.** Not because the machine is wrong,
   but because when a resident complains, someone accountable must have looked.
4. **Never ask a model to do something `pikepdf` can do exactly.** Deterministic tools
   for structure and validation; models only for judgment.
5. **No claim ships to a customer that isn't in the eval harness.**
