# The 30-day test

The point of the 30 days is not to build the company. It's to **find out, cheaply, which
of two worlds you're in** — and if it's the bad one, to have spent a month and learned it
for free.

## Week 1 — Scanner
Build the crawler, the WCAG audit, and the report generator. Run it on **twenty Colorado
special districts.**

**Deliverable:** a sales tool and a prospect list where every entry has a specific number
about that specific entity.

This is the only part that has to exist before you know anything.

## Week 2 — Eval harness *(no remediation code yet)*
Assemble the ground truth set. Build the harness. Pay a professional remediator for
properly-fixed reference documents.

**Deliverable:** the ability to state an honest pass rate by document type.

Resist the urge to write the pipeline first. The pipeline without the harness is a
number you can't trust attached to a margin you can't predict.

## Week 3 — Triage + the easy path
Triage classifier plus the easy path, measured against the harness. Find out the real
pass rate on **agendas and minutes** — the highest-volume and simplest document type.

**Deliverable:** a measured pass rate on the document type that dominates volume.

## Week 4 — Send twenty free audits

**Deliverable:** meetings, or the absence of them.

## The scoreboard

| Outcome | Read |
|---|---|
| **2+ entities take a meeting** | You have a business |
| **0 take a meeting** | You spent a month and learned it for free |

## After the 30 days, in order

1. **The review tool** — it's the gross margin lever ([`human-in-the-loop.md`](human-in-the-loop.md))
2. **Hard document types** — budgets with merged-cell tables, then scans
3. **The customer portal** — before/after, compliance report, audit log

## Prerequisites before the first paid engagement

Not week-numbered, but blocking:
- Lawyer-drafted engagement terms
- Errors and omissions coverage

See [`risks.md`](risks.md).
