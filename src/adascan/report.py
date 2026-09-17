"""Audit report generation.

The report is the sales motion: a specific number about a specific entity,
next to a legal deadline. Everything it asserts must be defensible — it goes
to a government attorney, not a marketer.

Hard rules (CLAUDE.md):
  - Never state that an entity or document *is compliant*. Report findings.
  - Cost figures are a market-rate range, labelled as such, never a quote.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from adascan.store import Store

# docs/sources.md rows 9 and 2 — verify before any report leaves the building.
MANUAL_RATE_LOW = 5.00
MANUAL_RATE_HIGH = 25.00

DEADLINE_LARGE = date(2027, 4, 26)   # entities serving 50,000+
DEADLINE_SMALL = date(2028, 4, 26)   # under 50,000, and all special districts

COMPLEXITY_ORDER = ("easy", "moderate", "hard", "decline", "unknown")


@dataclass
class Findings:
    domain: str
    run_id: int
    pages_crawled: int
    documents: int
    pdfs_analyzed: int
    untagged: int
    scanned: int
    no_language: int
    no_title: int
    total_pdf_pages: int
    by_type: dict[str, int]
    by_complexity: dict[str, int]
    errors: int
    partial: bool
    note: str

    @property
    def fail_rate(self) -> float:
        if not self.pdfs_analyzed:
            return 0.0
        return self.untagged / self.pdfs_analyzed

    def market_rate_range(self) -> tuple[float, float]:
        return (
            self.total_pdf_pages * MANUAL_RATE_LOW,
            self.total_pdf_pages * MANUAL_RATE_HIGH,
        )


def collect(store: Store, run_id: int) -> Findings:
    conn = store.conn
    run = store.run(run_id)
    if run is None:
        raise ValueError(f"no such run: {run_id}")

    counts = store.counts(run_id)
    triage_rows = list(conn.execute("SELECT * FROM pdf_triage WHERE run_id=?", (run_id,)))

    by_type: dict[str, int] = {}
    by_complexity: dict[str, int] = {}
    untagged = scanned = no_lang = no_title = total_pages = errors = 0

    for row in triage_rows:
        by_type[row["doc_type"] or "unknown"] = by_type.get(row["doc_type"] or "unknown", 0) + 1
        key = row["complexity"] or "unknown"
        by_complexity[key] = by_complexity.get(key, 0) + 1
        if row["error"]:
            errors += 1
            continue
        total_pages += row["pages"] or 0
        if not row["tagged"]:
            untagged += 1
        if row["scanned"]:
            scanned += 1
        if not row["has_lang"]:
            no_lang += 1
        if not row["has_title"]:
            no_title += 1

    return Findings(
        domain=run["domain"],
        run_id=run_id,
        pages_crawled=counts.get("html", 0),
        documents=sum(counts.get(k, 0) for k in ("pdf", "document")),
        pdfs_analyzed=len(triage_rows),
        untagged=untagged,
        scanned=scanned,
        no_language=no_lang,
        no_title=no_title,
        total_pdf_pages=total_pages,
        by_type=by_type,
        by_complexity=by_complexity,
        errors=errors,
        partial=run["status"] == "partial",
        note=run["note"] or "",
    )


def render_markdown(f: Findings, entity_name: str = "", large_entity: bool = False) -> str:
    name = entity_name or f.domain
    deadline = DEADLINE_LARGE if large_entity else DEADLINE_SMALL
    low, high = f.market_rate_range()
    days = (deadline - date.today()).days

    lines = [
        f"# Web accessibility findings — {name}",
        "",
        f"Scan of `{f.domain}` · run {f.run_id} · {date.today().isoformat()}",
        "",
        "## What was scanned",
        "",
        f"- **{f.pages_crawled:,}** web pages",
        f"- **{f.documents:,}** linked documents",
        f"- **{f.pdfs_analyzed:,}** PDFs analyzed, totalling **{f.total_pdf_pages:,}** pages",
        "",
    ]

    if f.partial:
        lines += [
            "> **Partial scan.** The crawl stopped early and these counts are a floor, "
            f"not a total. {f.note}",
            "",
        ]

    lines += [
        "## Findings",
        "",
        "| Finding | Documents | Share |",
        "|---|---:|---:|",
        _row("Untagged (no structure tree)", f.untagged, f.pdfs_analyzed),
        _row("Image-only, no text layer", f.scanned, f.pdfs_analyzed),
        _row("No document language set", f.no_language, f.pdfs_analyzed),
        _row("No document title set", f.no_title, f.pdfs_analyzed),
        "",
        "An untagged PDF cannot convey headings, reading order or table structure "
        "to a screen reader. Under WCAG 2.1 Level AA, which is the standard named "
        "in the ADA Title II rule, that is a failure.",
        "",
        "## By document type",
        "",
        "| Type | Documents |",
        "|---|---:|",
    ]
    for doc_type, count in sorted(f.by_type.items(), key=lambda kv: -kv[1]):
        lines.append(f"| {doc_type} | {count:,} |")

    lines += [
        "",
        "## By remediation difficulty",
        "",
        "| Tier | Documents | Meaning |",
        "|---|---:|---|",
    ]
    meanings = {
        "easy": "structural automation, sample-reviewed",
        "moderate": "automation with targeted human review",
        "hard": "substantial human review — large or table-heavy",
        "decline": "scans, fillable forms and maps — priced separately",
        "unknown": "not yet analyzed",
    }
    for tier in COMPLEXITY_ORDER:
        if tier in f.by_complexity:
            lines.append(f"| {tier} | {f.by_complexity[tier]:,} | {meanings[tier]} |")

    lines += [
        "",
        "## Deadline",
        "",
        f"**{deadline.isoformat()}** — {days:,} days from today.",
        "",
        "US Department of Justice, ADA Title II web accessibility rule. The standard "
        "is WCAG 2.1 Level AA. "
        + (
            "Entities serving 50,000 or more people."
            if large_entity
            else "Entities serving fewer than 50,000 people, and all special "
            "districts regardless of size."
        ),
        "",
        "## What remediation costs at market rate",
        "",
        f"At the prevailing manual rate of ${MANUAL_RATE_LOW:.0f}–${MANUAL_RATE_HIGH:.0f} "
        f"per page, the **{f.total_pdf_pages:,}** pages above represent",
        "",
        f"### ${low:,.0f} – ${high:,.0f}",
        "",
        "This is the published market range for human remediation, shown so the scale "
        "is visible. It is not a quote and does not reflect what this work would be "
        "priced at.",
        "",
        "---",
        "",
        "### Scope and limits of this report",
        "",
        "- Automated structural analysis only. It reports what machine checks can "
        "establish: whether a document has a structure tree, a text layer, a language "
        "and a title.",
        "- Automated checking catches roughly 30–40% of WCAG issues. A document that "
        "passes every check here may still be unusable in practice, and confirming "
        "otherwise requires human review.",
        "- **This report does not determine compliance.** It is not a legal opinion "
        "and does not certify any document or website as conforming.",
        "- Counts reflect what was publicly reachable by crawling on the date shown. "
        "Documents behind logins, search forms, or `robots.txt` exclusions are not "
        "included.",
    ]
    if f.errors:
        lines.append(
            f"- **{f.errors:,}** documents could not be opened for analysis and are "
            "excluded from the findings above."
        )

    return "\n".join(lines) + "\n"


def _row(label: str, count: int, total: int) -> str:
    share = f"{count / total * 100:.0f}%" if total else "—"
    return f"| {label} | {count:,} | {share} |"


def write_report(
    store: Store,
    run_id: int,
    out_dir: Path,
    entity_name: str = "",
    large_entity: bool = False,
) -> tuple[Path, Path]:
    """Write markdown and JSON reports. Returns both paths."""
    findings = collect(store, run_id)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    stem = f"{findings.domain.replace('.', '_')}_run{run_id}"
    md_path = out_dir / f"{stem}.md"
    json_path = out_dir / f"{stem}.json"

    md_path.write_text(render_markdown(findings, entity_name, large_entity), encoding="utf-8")
    json_path.write_text(
        json.dumps(findings.__dict__, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )
    return md_path, json_path
