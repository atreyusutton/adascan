# TODO

Running state. Update as things move.

## Done
- [x] Repo initialized, thesis captured in `docs/`

## In progress
- _nothing yet_

## Next — Week 1 (scanner)
- [ ] Decide crawl policy: rate limits, robots.txt, user-agent identification, backoff
- [ ] Async crawler: inventory HTML pages + PDF links (URL, content hash, bytes, Last-Modified)
- [ ] axe-core via Playwright on HTML pages
- [ ] PDF triage checks (StructTreeRoot present? text layer? page/image/table counts? form fields? linearized?)
- [ ] Audit report generator: doc count, fail count, severity breakdown, market-rate cost, deadline
- [ ] Enumerate Colorado special districts from the state website registry — verify it's machine-readable
- [ ] Run on 20 Colorado special districts

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
