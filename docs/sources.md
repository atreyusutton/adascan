# Sources and verification status

Every grounded claim in this repo, with a verification column. **Nothing here has been
independently verified in-repo yet** — the claims come from prior research and are
recorded so they can be checked, cited, and re-checked when regulation moves.

Anything used in a customer-facing audit report must be verified and citable first.

| # | Claim | Used in | Verified in repo |
|---|---|---|---|
| 1 | DOJ Title II deadline extension (April 2026) | opportunity | ☐ |
| 2 | Deadlines: Apr 26 2027 (≥50k), Apr 26 2028 (<50k + all special districts) | opportunity, roadmap | ☐ |
| 3 | Standard is WCAG 2.1 Level AA | opportunity | ☐ |
| 4 | DOJ cited limits of generative AI for remediation as a reason for the extension | opportunity, risks, architecture | ☐ |
| 5 | 90,837 US local governments (3,031 counties / 35,705 municipalities+townships / 12,546 school districts / 39,555 special districts) | opportunity, economics | ☐ |
| 6 | Colorado has 3,141 local governments (333 general purpose, 2,808 special districts) | opportunity | ☐ |
| 7 | Colorado HB21-1110 applies to state/local entities; deadline passed; $3,500 per violation payable to plaintiffs | opportunity, risks | ☐ |
| 8 | Colorado special district / post-2000 metro district website requirements make targets enumerable | opportunity, open-questions | ☐ |
| 9 | Manual PDF remediation sells for $5–$25 per page | opportunity, economics | ☐ |
| 10 | veraPDF: free, open source, PDF Association + Open Preservation Foundation, CLI + Docker, implements Matterhorn Protocol | architecture | ☐ |
| 11 | Matterhorn Protocol: 31 checkpoints, 136 failure conditions; ~half require human checks | architecture, eval-harness | ☐ |
| 12 | Automated accessibility checkers catch ~30–40% of WCAG violations | architecture | ☐ |
| 13 | Adobe PDF Accessibility Auto-Tag API free tier: 500 documents/month | architecture | ☐ |
| 14 | PDFix SDK is enterprise-tier, quote-based | architecture | ☐ |
| 15 | pikepdf wraps QPDF and exposes the PDF object model | architecture | ☐ |
| 16 | axe-core is the standard automated web accessibility rule engine | architecture | ☐ |
| 17 | Incumbents: Allyant, Equidox, CommonLook, Level Access | risks | ☐ |
| 18 | Overlay widget vendors have a poor reputation and face litigation | risks | ☐ |

## Claims marked `[E]` (estimates)

Not listed here individually — they're marked inline in each doc. The ones that actually
move the outcome are collected in [`economics.md`](economics.md) under "The four things
that actually decide the number." Treat everything else as scaffolding.

## Notes

- Regulation moves. Re-check rows 1–3 and 7 before every outreach batch, and note the
  check date in this file.
- Rows 9 and 13 set pricing and cost floors respectively — verify before quoting anyone.
- Rows 11 and 12 are the intellectual basis for the "judgment layer" thesis in
  [`architecture.md`](architecture.md). If they're wrong, the thesis weakens.
