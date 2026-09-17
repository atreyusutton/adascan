# Architecture

Four separable systems. Build order is **scanner → eval harness → pipeline → review tool**
(see [`roadmap.md`](roadmap.md) for why).

## The pipeline, stage by stage

### Stage 0 — Discovery *(ships first; this is the sales tool)*
An async crawler walks a domain, respects `robots.txt`, and records every HTML page and
every PDF link with:
- URL
- content hash
- byte size
- `Last-Modified` header

For the HTML side, run **axe-core** through **Playwright** on each page.

**Output:** an inventory table and a findings table. That's it. That's the free audit
that gets meetings.

### Stage 1 — Triage
For each PDF, **cheap deterministic checks first, before spending a token**:
- Is there a `StructTreeRoot` at all — is this tagged in any way?
- Is there a text layer, or is this a scan?
- Page count, image count, count of table-like regions
- Does it have form fields? Is it linearized?

Then classify: **document type** (agenda, minutes, budget, resolution, map, fillable
form, newsletter) and **complexity tier**.

> **Triage is where margin is won or lost.** Misrouting one 400-page board packet into
> the easy path costs more than a hundred correctly routed documents earned. Spend real
> effort here.

### Stage 2 — Understanding
- Render each page to an image with **PyMuPDF**
- Send the image to a **vision model** and ask for logical structure: what's a heading
  and at what level, where the column boundaries are, where a table starts and ends and
  which cells are headers, which images are meaningful vs. decorative (borders, logos)
- Separately pull text **with coordinates** from PyMuPDF — so you have both *what it
  says* and *exactly where it sits*
- **Reconcile the two**
- For scans: OCR first, and **flag the document**, because OCR errors propagate into tags

### Stage 3 — Tagging *(hardest part to build)*
Build the structure tree and write it into the PDF:
- **pikepdf** (wraps QPDF) for direct access to the PDF object model — needed because
  you're writing `StructTreeRoot` and marked-content references by hand
- Set reading order
- Attach alt text
- Tag tables with proper header scope
- Set document language, title, and the display-title flag

**Start with a baseline, not a rewrite.** `[G]` Use Adobe's **PDF Accessibility
Auto-Tag API** as the baseline tagger — free for **500 documents/month**. Spend early
effort measuring *where it fails* rather than rebuilding it. Replace it only once you
know exactly what it gets wrong on your document mix.

`[G]` **PDFix** sells an automated-tagging SDK too, but it's enterprise-tier and
quote-based — a later decision.

### Stage 4 — Validation
`[G]` Run **veraPDF** against **PDF/UA-1**. Free, open source, maintained by the PDF
Association and the Open Preservation Foundation, has a CLI and a Docker image, and
implements the full **Matterhorn Protocol: 31 checkpoints, 136 failure conditions.**

That's your automated grader and it costs nothing.

`[G]` Note the ceiling: about **half of Matterhorn's 136 failure conditions require
human eyes.** veraPDF passing is necessary, not sufficient.

### Stage 5 — Human review
See [`human-in-the-loop.md`](human-in-the-loop.md). The part everyone underestimates.

### Stage 6 — Delivery
Write the files back, and give the customer:
- A portal showing **before and after**
- A **compliance report** they can hand to their attorney
- An **audit log** of exactly what changed on which document and who approved it

> The audit log is not a nice-to-have. It's what they show when someone complains.

## The stack

| Layer | Choice | Why |
|---|---|---|
| Customer-facing app | **Next.js on Vercel** + **Neon Postgres** | The portal is a normal CRUD app |
| Workers | **Python**, on a rented dedicated box or **Fly.io** — *not* on Vercel | PDF rendering is CPU/memory heavy and runs for minutes. `[E]` A ~$60/mo dedicated server with real cores out-throughputs a small fortune of serverless on this workload |
| Queue | **Postgres-backed** | One less system; workers pull jobs |
| Object storage | **Cloudflare R2** | No egress charges — matters once you're shipping fixed PDFs back |
| PDF object writes | **pikepdf** | Direct object model access |
| Render + coordinate text | **PyMuPDF** | |
| Repair malformed input | **Ghostscript** | Government PDFs are frequently broken in boring ways |
| OCR | **Tesseract** or a cloud OCR | For scans |
| PDF validation | **veraPDF** CLI in Docker | PDF/UA-1 + Matterhorn |
| Web validation | **axe-core** via **Playwright** | |
| Models | A **vision model** for page layout and alt text; a **cheap fast model** for bulk triage and classification | **Route by complexity. Don't send everything to the expensive model** — per-page cost is mostly determined by how disciplined this routing is |

## Where the AI actually goes, and why this works now

`[G]` Automated accessibility checkers catch roughly **30–40% of WCAG violations**. The
other 60–70% need human judgment. `[G]` About half of Matterhorn's 136 failure
conditions need human eyes too.

**But those numbers describe rule checkers.** A rule checker can tell you alt text is
missing; it cannot tell you whether *"image of person"* is a useful description. It can
verify a tag sequence is valid; it cannot tell you whether reading that sequence aloud
makes any sense.

That gap — between **structurally valid** and **actually meaningful** — is exactly where
a language model is good and a rule engine is useless.

`[E]` That's the thesis for why this is possible in 2026 and wasn't in 2022, and why DOJ
can correctly say AI isn't there yet while the opportunity is still real: the incumbents
are running rule checkers plus offshore labor, and nobody has properly built the
**judgment layer** in between.

### Division of labor

| Job | Owner |
|---|---|
| Parsing, writing objects, checking conformance | **Deterministic tools.** Never ask a model to do something pikepdf can do exactly |
| What is this document? Is this image meaningful or decorative? What does this chart say? Does this reading order make sense? Is this table's header row actually the header row? | **Models — judgment only** |
| The residual, and accountability | **Humans** |

## Where it breaks

Known-hard, in rough order of how much they'll cost you:

1. **Scanned documents with no text layer** — OCR errors compound into wrong tags.
   Price separately or decline.
2. **Tables with merged cells and column spans** — genuinely hard, and common in
   **budgets**, which are exactly the documents people care most about.
3. **Maps and engineering drawings** — there often *is* no good alt text for a zoning
   map. The correct answer is a text alternative published alongside it. That's a
   conversation with the customer, not an automation problem, and pretending otherwise
   is how you deliver something useless.
4. **400-page board packets** — chunk by page, then do a document-level structure pass
   to stitch it together, or you'll blow memory and context both.
5. **Fillable forms** — their own world of pain. Leave for later.
6. **Regressions** — a model update silently changes your outputs. Without the eval
   harness running on every change, you find out when a customer does.
