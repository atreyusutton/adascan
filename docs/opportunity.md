# The opportunity

> **Legend:** `[G]` = grounded, sourced claim. `[E]` = estimate/assumption, to be stress-tested.
> See [`sources.md`](sources.md) for verification status of every `[G]`.

## The regulatory setup

`[G]` In April 2026 the DOJ pushed its ADA **Title II** web accessibility compliance
deadlines to:

| Entity | Deadline |
|--------|----------|
| Public entities serving **50,000 or more** people | **April 26, 2027** |
| Public entities serving **fewer than 50,000** | **April 26, 2028** |
| **Every special district, regardless of size** | **April 26, 2028** |

`[G]` The technical standard is **WCAG 2.1 Level AA**.

## The market

`[G]` There are **90,837 local governments** in the United States:

| Type | Count |
|------|-------|
| Counties | 3,031 |
| Municipalities and townships | 35,705 |
| School districts | 12,546 |
| Special districts | 39,555 |
| **Total** | **90,837** |

Essentially all of them are covered by Title II. `[E]` Essentially none are ready.

## The detail that makes this different

`[G]` When DOJ explained why it granted the extension, one of the reasons it listed
was **the limits of generative AI for remediation**.

A federal agency publicly documented that the technology cannot yet do the thing it is
legally requiring tens of thousands of entities to do by a fixed date. That is a
mandated market with a stated capability gap and a countdown clock on it.

This cuts both ways and both directions matter:

- **For:** demand is compelled by law, not persuasion. The opening line is *"you have
  to do this by April 2027 and I can show you exactly how far behind you are."* The
  buyer has a deadline, a documented standard, and personal liability.
- **Against:** DOJ is right. Automated remediation is not solved. See
  [`risks.md`](risks.md) — this is the first and largest risk, not a footnote.

## The cost arbitrage

`[G]` Manual PDF remediation runs roughly **$5 to $25 per page**, performed by human labor.

`[E]` A mid-size city has tens of thousands of pages of agendas, minutes, budgets,
permits, and forms. Marginal pipeline cost per page is cents. That gap is the whole
business. See [`economics.md`](economics.md) for the arithmetic and the point at which
the gap closes.

## Why it recurs

Governments publish new documents every single week. The backlog is a project; the
ongoing flow is a subscription a city cannot cancel without becoming non-compliant
again. `[E]` But see [`economics.md`](economics.md): recurring revenue is only about
**20–25%** of year-one revenue. Model this as a windfall with an annuity attached, not
as SaaS.

## Why Colorado first

`[G]` **HB21-1110** already applies to state and local entities in Colorado, its
deadline has already passed, and it carries a **$3,500-per-violation** penalty payable
directly to plaintiffs. Colorado governments are exposed *right now*, not in 2027.

`[G]` Colorado has **3,141 local governments**: 333 general purpose, 2,808 special districts.

`[E]` **Apply a hard haircut.** Do not treat 2,808 special districts as 2,808 prospects.
A large share are shell metro districts covering a single subdivision, with a five-page
website and essentially no documents. Assume **20–30% are real prospects** — call it
**600 to 800** in Colorado.

`[G]` The upside: they're unusually easy to enumerate. Colorado metro districts formed
after 2000 with taxing authority are required by statute to have a public website, and
all special districts must register a website with the state in order to post meeting
notices electronically. Many are on `colorado.gov` subdomains.

**Implication:** there is a public, enumerable list of hundreds of target websites you
can crawl in a weekend and produce a real page count and a real dollar figure for every
one of them before talking to a single person.

`[G]` HB21-1110 does not depend on DOJ, so Colorado demand survives another federal
deadline slip.

Secondary advantage: `[E]` you can drive to these meetings.

## The wedge

**Do not start by selling remediation. Start by building the audit.**

Point a crawler at a government domain, inventory every page and every PDF, test
against WCAG 2.1 AA, and generate a report that says:

> You have 14,200 documents. 9,300 of them fail. Here is the breakdown by severity.
> Here is what the market rate to fix it would cost you. Here is your deadline.

Run that across every municipality, school district and special district in Colorado in
a weekend. The output is a ranked prospect list where **each entry comes with a
specific number about that specific entity.**

Free audit → specific finding → legal deadline. That is the entire sales motion and it
costs compute.

Then sell remediation at a fraction of the manual rate, delivered by the pipeline, with
human review on the documents that actually need it.
