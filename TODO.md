# TODO

Running state. Update as things move.

## Done
- [x] Repo initialized, thesis captured in `docs/`
- [x] Crawl policy decided and documented (`docs/crawl-policy.md`)
- [x] Async crawler: inventory HTML pages + documents (URL, sha256, bytes, Last-Modified)
- [x] PDF triage: StructTreeRoot, text layer, images, table regions, form fields, linearized, lang, title
- [x] Complexity routing (easy / moderate / hard / decline) and document-type classification
- [x] Audit report generator (markdown + JSON), with market-rate range and deadline
- [x] SQLite inventory store; `adascan` CLI (crawl / triage / report / runs)
- [x] Integration tests against a local fixture site — 28 passing

## In progress
- _nothing yet_

## Next — Week 1 remainder (scanner)
- [ ] axe-core via Playwright on HTML pages — the WCAG side is not built yet
- [ ] Enumerate Colorado special districts from the state website registry — verify it's machine-readable
- [ ] Run on 20 Colorado special districts
- [ ] Batch runner: take a seed list, crawl N domains, emit a ranked prospect table
- [ ] Decide retention/deletion policy for downloaded documents before any bulk run

## Next — Week 2 (eval harness, no remediation code)
- [ ] Assemble 300–500 real government PDFs, stratified by type and complexity
- [ ] Commission ground truth from a professional remediator
- [ ] veraPDF in Docker, wired to run per-document
- [ ] Metrics: PDF/UA pass rate by type, tag tree agreement, reading order, alt text quality (human + calibrated judge), **human minutes per page**
- [ ] CI: harness runs on every change

## Week 3 (triage + easy path)
- [ ] Document type classifier
- [ ] Easy path: agendas and minutes, measured against the harness
- [ ] Baseline against Adobe Auto-Tag API; record where it fails

## Week 4 (outreach)
- [ ] Send 20 free audits
- [ ] Scoreboard: 2+ meetings = business, 0 = learned it for free

## Blocking before first paid engagement
- [ ] Lawyer-drafted engagement terms (what exactly is being certified?)
- [ ] Errors and omissions coverage bound

## Verification backlog
- [ ] Verify all `[G]` claims in `docs/sources.md`, note check dates
