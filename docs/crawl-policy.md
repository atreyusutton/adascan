# Crawl policy

Binding operational rules for any adascan crawl of a real government domain.
Resolved before the crawler was written, per `CLAUDE.md`.

These entities are small, often on cheap shared hosting, and are the people we
intend to sell to. Taking a fire district's website down is a permanent way to
lose a customer and the fastest way to make this look like an attack.

## Identity

Every request carries a User-Agent naming the crawler and a contact address:

```
adascan/0.1 (+https://github.com/atreyusutton/adascan; contact: <CONTACT_EMAIL>)
```

`ADASCAN_CONTACT` must be set or the crawler refuses to start. An anonymous
crawler hitting hundreds of `.gov` domains is indistinguishable from
reconnaissance.

## robots.txt

- Fetched once per host, cached for the run, parsed with `urllib.robotparser`.
- **A disallowed URL is not fetched.** No exceptions, including for PDFs.
- `Crawl-delay` is honored when present and **raises** our delay; it never
  lowers it below the floor.
- A malformed or unreachable `robots.txt` is treated as *allow*, matching
  standard behavior — but the failure is recorded in the run log.

## Rate limits

| Setting | Default | Notes |
|---|---|---|
| Delay between requests, per host | **1.0 s** | floor; `Crawl-delay` can raise it |
| Max concurrent requests, per host | **2** | |
| Max concurrent hosts | **8** | tune down before tuning host concurrency up |
| Request timeout | **30 s** | |
| Max pages per host | **5,000** | safety stop, overridable per run |

Concurrency is enforced per host, not globally, so one slow site can't be
starved by a fast one and a fast site can't be hammered.

## Backoff

- **429** — honor `Retry-After` if present, else exponential backoff from 5 s,
  doubling, capped at 120 s. Three strikes and the host is abandoned for the run.
- **5xx** — same backoff schedule. A site returning 500s is a site in trouble;
  do not keep pushing.
- **Connection errors** — two retries, then record and move on.
- Abandoning a host is recorded as a partial result, never silently dropped. A
  partial inventory that claims to be complete is worse than no inventory.

## Scope

- Same registrable domain as the seed only. Subdomains are followed;
  third-party links are recorded but never fetched.
- `GET` only. Never `POST`, never a form submission, never an authenticated
  request, never anything behind a login.
- PDFs and other documents are fetched with a size cap (**default 150 MB**) and
  streamed to disk.
- Query-string URLs are normalized and deduplicated by content hash to avoid
  walking calendar and pagination traps.

## What is never stored in git

Crawl output — inventories, downloaded documents, reports — goes to `data/`,
which is gitignored. Government PDFs are usually public records, but personnel
files, unredacted records and PII in permits do appear. See
`docs/open-questions.md` for the unresolved retention and deletion policy.

## Kill switch

`ADASCAN_DRY_RUN=1` issues **no HTTP requests at all**. It resolves the seed,
records it, and exits.

Its purpose is to validate configuration, scope and contact details before a
seed list is pointed at anything real. It deliberately does **not** report how
large a site is: link discovery requires fetching and parsing HTML, so a dry run
cannot expand the frontier past the seed. Do not read a one-page dry run as
evidence that a site is small.
