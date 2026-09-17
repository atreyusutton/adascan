# Open questions

Things the thesis does not currently answer. Written down so they get answered
deliberately rather than discovered late. *(Added during repo setup — these are
questions raised by the material, not claims from it.)*

## Blocking before any paid work

- **Engagement terms and E&O coverage.** Who drafts them, what do they cost, how long
  does the coverage take to bind? This gates the first invoice, not the first line of
  code. → [`risks.md`](risks.md)
- **What exactly are you certifying?** "Compliant" is a word with legal weight. Is the
  deliverable *"PDF/UA-1 validated + human reviewed"*, or something stronger? The answer
  determines the liability exposure and belongs in the engagement terms verbatim.

## Blocking before pricing anything

- **The pass rate, by document type.** Everything else is noise next to it.
  → [`eval-harness.md`](eval-harness.md)
- **What does the review tool actually get a reviewer down to?** The 3 min → 30 sec
  target is an aspiration with no evidence behind it yet. It's the second-largest
  margin lever and it's currently unmeasured.
- **What fraction of a real government's corpus is the stuff you're best at?** If
  agendas and minutes are 80% of pages, a 95% pass rate there carries the business even
  if budgets are terrible. If budgets and scans dominate, it doesn't. The scanner should
  answer this from real inventories in week one — before the pipeline exists.

## Blocking before scaling

- **Crawling posture.** Rate limits, `robots.txt`, identifying the crawler, and what
  happens when a small district's site falls over. Crawling hundreds of government
  domains unannounced is a reputational and possibly legal surface. Decide the policy
  before the weekend run, not after a complaint.
- **Handling the documents themselves.** Government PDFs are usually public records, but
  not always — personnel files, unredacted records, and PII in permits do appear.
  Retention, storage location, and deletion policy need to exist before bulk
  downloading. `data/` and `corpus/` are gitignored; that's a start, not a policy.
- **Enumerating Colorado.** The special district website registry is the claimed source
  of an enumerable target list. Is it actually machine-readable, current, and complete?
  The entire week-one plan assumes yes.

## Unanswered strategically

- **What happens after April 2028?** The recurring annuity is 20–25% of year-one
  revenue and the urgency collapses. Converting the customer base into something else
  is named as the only path to a compounding business, and that something else has not
  been identified. Candidates worth thinking about, none validated: ongoing web
  accessibility monitoring rather than just PDFs; becoming the document publishing
  pipeline itself rather than a remediation layer bolted on afterward; expanding to
  other Title II obligations; selling the eval harness / measurement capability
  separately.
- **Build vs. resell on tagging.** Adobe's Auto-Tag API is the baseline. If it turns out
  to be good enough on the dominant document types, the business is a distribution and
  measurement company, not a tagging company — which is a *better* business, not a
  worse one, but a different one. Decide this from harness data, not preference.
- **Does the free-audit motion survive contact?** The whole sales thesis rests on an
  unsolicited report producing meetings. Week four tests it once, at n=20. That's enough
  to see a signal, not enough to trust a rate.
