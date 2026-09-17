# Economics

> **Legend:** `[G]` grounded/sourced · `[E]` estimate. Almost everything below is `[E]`.
> The honest summary: **it depends almost entirely on close rate and automation pass rate.**

## Unit economics

`[E]` Per-page cost, assuming the pipeline works:

| Component | Cost/page | Basis |
|-----------|-----------|-------|
| Compute (models, render, validate) | $0.05 | pennies if triage routing is disciplined |
| Human review | $0.25 | 20% of pages × 3 min × $25/hr contractor |
| **All-in (rounded up)** | **$0.30** | |

`[G]` Manual market rate: **$5–$25/page**.

`[E]` Sell at **$1.75/page** → roughly **80% gross margin** while undercutting the
manual market by 75%+.

### The sensitivity that is the entire business

| Share of pages needing a human | Cost/page | Margin at $1.75 | What you are |
|---|---|---|---|
| 20% | ~$0.30 | ~80% | a software business |
| 50% | ~$1.30 | ~26% | a staffing agency |

You cannot know which until you build the test set and measure it. That is why the
[eval harness](eval-harness.md) is week two, not week ten.

## What a customer is worth

`[E]` All figures estimates.

### Small special district (metro, fire, water)
- 500–2,000 pages of minutes, budgets, audits, notices
- Backlog: **~$2,500** · Ongoing: **~$150/mo**
- Year 1 ≈ **$4,300** · Year 2+ ≈ **$1,800/yr**

### Small town or small school district
- ~10,000 pages
- Backlog: **~$17,500** at a volume rate · Ongoing: **~$400/mo**
- Year 1 ≈ **$22,000** · Year 2+ ≈ **$5,000/yr**

### Mid-size city, county, or large district
- 50,000+ pages
- Backlog: **~$60,000** · Ongoing: **~$1,500/mo**
- Year 1 ≈ **$78,000** · Year 2+ ≈ **$18,000/yr**
- **Caveat:** goes through an RFP, 6–12 months to close. Do not build year one on these.

## Scenarios

`[E]` All three.

| Scenario | Accounts | Revenue | Recurring underneath |
|---|---|---|---|
| **12 months, part-time (in school)** | 12 special districts + 3 small towns | ~$118k booked | ~$40k |
| **24 months full-time**, CO + 2 neighboring states | 60 SDs + 20 towns/school districts + 4 mid-size | ~$970k in year 2 | ~$250k |
| **Team, through the 2028 deadline** | 300 entities @ $12k blended | ~$3.6M | ~$900k |

**Haircut the first scenario** for deals that slip: call it **$50k–$100k**. That's an
outcome where you graduate with a running business instead of a summer internship.

The 24-month scenario needs one or two people on review/QA and probably sales help.

**Theoretical ceiling:** 90,837 entities × even $20k one-time = a **$1.8B pool**. But
capturing a meaningful slice means competing with funded companies and hiring fast.
Treat the ceiling as context, never as a plan.

### Honest expectation

- First 12 months while in school, executing well: **$40k–$100k**
- 24 months full-time after graduating: **$500k–$1.5M**
- Ceiling with a team through 2028: **high single-digit millions**
- **Failure mode: near zero** — because the pass rate isn't good enough and every job
  needs more human labor than the price supports.

## The four things that actually decide the number

Everything else is noise next to these.

### 1. Automation pass rate
The whole business. 80% automated → 80% margin. 50% → staffing agency. Unknowable
until measured. See [`eval-harness.md`](eval-harness.md).

### 2. Revenue is front-loaded and then falls off a cliff
Fixing a district's twenty-year archive is a one-time job. You bill it once and never
again. The recurring piece is only **20–25% of year-one revenue**.
**Do not model this as SaaS.** Model it as a windfall with an annuity attached.

### 3. The deadline is the demand
April 2027 and April 2028 are what make anyone move. After that, urgency collapses and
you're selling a nice-to-have. There is roughly a **24-month window at peak intensity**.
That's a real business — a "make a lot of money in two years" business, not a
compounding one, *unless you convert the customer base into something else before the
window closes.* That conversion is an open question, not a plan. See
[`open-questions.md`](open-questions.md).

### 4. Government budget calendars
The thing that surprises everyone. `[E]` Entities adopt budgets in the fall for the next
calendar year. A district that wants to buy in March often has **no money until January**.
Your sales cycle is dictated by their budget cycle, not your effort.

**Operational consequence:** free audits should land *before* budget adoption season so
the line item exists when they write the budget. Time the outreach to their calendar.
