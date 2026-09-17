# CLAUDE.md — working rules for adascan

Written for Artax (and any agent) working unattended in this repo. Read before
touching anything. The rules below exist because this project sells a legal
compliance claim to government entities; the failure mode is not a broken build,
it's certifying something non-compliant and inheriting a customer's liability.

## What this repo is right now

**Documentation only. No code yet.** `docs/` holds the business thesis and the
system design. Everything in it is argued, not settled. Start at `README.md`,
then `docs/roadmap.md` for what happens next, then `TODO.md` for running state.

## The rules that are not negotiable

### 1. Mark every claim `[G]` or `[E]`
`[G]` = grounded, sourced, verifiable. `[E]` = estimate or assumption.

Every factual claim in `docs/` carries one of these markers. When you add a
claim, mark it. When you turn an estimate into a verified fact, move it and tick
its row in `docs/sources.md`. **Never let a number migrate from `[E]` to `[G]`
without a source.** This convention is the whole defense against a pricing
assumption quietly becoming something we tell a customer.

### 2. No claim ships that isn't in the eval harness
If the pipeline's output quality is asserted anywhere — a report, a README, a
customer-facing string — there must be a harness number behind it, measured **by
document type, never blended**. See `docs/eval-harness.md`.

### 3. Never promise full automation
DOJ's stated reason for extending the Title II deadline was the limits of
generative AI for remediation. Complex tables, scanned forms, maps and
multi-column layouts need a person. Every customer-facing artifact prices and
describes a **hybrid**. No exceptions, no softening of the language.

### 4. Do real remediation. Never overlay widgets.
Overlay vendors have a deservedly bad reputation and get sued. Do not implement,
reference, or suggest an overlay approach.

### 5. Never ask a model to do what a library does exactly
Deterministic tools (pikepdf, PyMuPDF, veraPDF, axe-core) for parsing, writing
objects, and checking conformance. Models **only** for judgment: what is this
document, is this image meaningful or decorative, does this reading order make
sense, is this row actually a header. Mixing these up is how you get outputs
that are unverifiable and expensive at the same time.

## Hard stops — do not do these unattended

Stop and write what you need into the PR description or `TODO.md` instead.

- **Never contact a real entity.** No email, no form submission, no phone, no
  outreach of any kind to a government body, employee, or vendor. Audit reports
  are generated and left for review; a human sends them.
- **Never make a compliance determination in shipped output.** You may report
  what a validator found. You may not say an entity or document "is compliant."
- **Never commit crawled documents, scan output, or corpus files.** `data/`,
  `corpus/`, `out/` and `*.pdf` are gitignored. Keep it that way. Government
  PDFs are usually public records but not always — personnel files, unredacted
  records and PII in permits do appear.
- **Never commit credentials**, API keys, or a customer list.
- **Don't set customer pricing or write legal/contractual language.** The numbers
  in `docs/economics.md` are `[E]` modelling, not a price sheet.

## Crawling posture

Before any crawl of a real government domain:
- Respect `robots.txt`.
- Rate limit conservatively. These are small entities on cheap hosting; taking a
  fire district's website down is a real and permanent way to lose a customer.
- Identify the crawler in the User-Agent with a contact address.
- Back off on 429/5xx rather than retrying hard.

The crawl policy is an open item in `docs/open-questions.md`. If it's still
unresolved when you get there, resolve it in a PR **before** writing the crawler,
not after.

## Decisions already made — don't re-litigate

Stated in `docs/architecture.md` with reasoning. Propose a change in a PR with
evidence if you disagree; don't quietly substitute something else.

- Next.js on Vercel + Neon Postgres for the customer-facing app
- Python workers **off** Vercel (dedicated box or Fly.io); Postgres-backed queue
- Cloudflare R2 for object storage
- pikepdf, PyMuPDF, Ghostscript, Tesseract/cloud OCR
- veraPDF (PDF/UA-1, Matterhorn) as the automated grader; axe-core via Playwright
- Adobe PDF Accessibility Auto-Tag API as the **baseline** tagger to measure
  against, not a component to rebuild before it's been measured
- Build order: scanner → eval harness → pipeline → review tool. This order is
  deliberate and is explained in `README.md`. Don't reorder it.

## Git workflow

- **Never commit to `main`.** Branch, commit, open a PR, leave it for review.
- Conventional commits: `feat:`, `fix:`, `chore:`, `refactor:`, `docs:`, `test:`.
- One logical change per commit.
- Never force-push. Never rewrite published history.
- Update `TODO.md` in the same PR as the work it describes.

## When you're unsure

Prefer opening a PR that states the question over guessing. An unresolved
question in a PR description costs a day. A confident wrong assumption about
accessibility conformance costs a customer.
