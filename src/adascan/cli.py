"""Command line interface.

    adascan crawl https://example.gov --out data/
    adascan triage --db data/adascan.db
    adascan report --db data/adascan.db --entity "Town of Example"
    adascan runs --db data/adascan.db
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from adascan import __version__
from adascan.config import ConfigError, CrawlConfig
from adascan.crawl import Crawler
from adascan.report import write_report
from adascan.store import Store
from adascan.triage import TriageUnavailable, triage_pdf

log = logging.getLogger("adascan")


def _setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)-5s %(message)s",
        datefmt="%H:%M:%S",
    )


def cmd_crawl(args: argparse.Namespace) -> int:
    try:
        config = CrawlConfig.from_env(
            delay_seconds=args.delay,
            per_host_concurrency=args.concurrency,
            max_pages_per_host=args.max_pages,
        )
    except ConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    data_dir = Path(args.out)
    store = Store(data_dir / "adascan.db")

    if config.dry_run:
        log.info(
            "DRY RUN — no requests will be issued. Link discovery needs fetched "
            "HTML, so only the seed is resolved; this validates config, scope "
            "and contact, not the size of the site."
        )

    log.info("crawling %s as %s", args.seed, config.user_agent)
    crawler = Crawler(args.seed, config, store, data_dir, max_depth=args.depth)

    try:
        run_id = asyncio.run(crawler.run())
    except KeyboardInterrupt:
        log.warning("interrupted — partial results retained")
        store.close()
        return 130

    counts = store.counts(run_id)
    log.info(
        "run %d complete: %d pages, %d pdfs, %d other documents",
        run_id, counts.get("html", 0), counts.get("pdf", 0), counts.get("document", 0),
    )
    store.close()
    print(run_id)
    return 0


def cmd_triage(args: argparse.Namespace) -> int:
    store = Store(args.db)
    run_id = args.run or (store.latest_run() or {})["id"]

    pdfs = [row for row in store.resources(run_id, "pdf") if row["local_path"]]
    if not pdfs:
        log.warning("no downloaded PDFs for run %d", run_id)
        store.close()
        return 1

    log.info("triaging %d PDFs from run %d", len(pdfs), run_id)
    analyzed = failed = 0
    for row in pdfs:
        try:
            result = triage_pdf(row["local_path"], url=row["url"], title=row["title"] or "")
        except TriageUnavailable as exc:
            print(f"error: {exc}", file=sys.stderr)
            store.close()
            return 2
        store.record_triage(run_id, row["url"], **result.as_row())
        analyzed += 1
        if result.error:
            failed += 1
        if analyzed % 50 == 0:
            store.commit()
            log.info("  %d/%d", analyzed, len(pdfs))

    store.commit()
    log.info("triage complete: %d analyzed, %d unreadable", analyzed, failed)
    store.close()
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    store = Store(args.db)
    latest = store.latest_run()
    if latest is None:
        print("error: no runs in database", file=sys.stderr)
        store.close()
        return 1
    run_id = args.run or latest["id"]

    md_path, json_path = write_report(
        store, run_id, Path(args.out), args.entity, args.large_entity
    )
    store.close()
    print(md_path)
    print(json_path)
    return 0


def cmd_runs(args: argparse.Namespace) -> int:
    store = Store(args.db)
    rows = store.conn.execute("SELECT * FROM runs ORDER BY id DESC LIMIT 20")
    print(f"{'id':>4}  {'status':<9} {'domain':<32} {'started':<20} note")
    for row in rows:
        print(
            f"{row['id']:>4}  {row['status']:<9} {row['domain'][:32]:<32} "
            f"{row['started_at'][:19]:<20} {row['note'] or ''}"
        )
    store.close()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="adascan", description=__doc__)
    parser.add_argument("--version", action="version", version=f"adascan {__version__}")
    parser.add_argument("-v", "--verbose", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)

    crawl = sub.add_parser("crawl", help="crawl a government domain")
    crawl.add_argument("seed", help="seed URL, e.g. https://example.gov")
    crawl.add_argument("--out", default="data", help="output directory (default: data)")
    crawl.add_argument("--delay", type=float, default=1.0, help="seconds between requests per host")
    crawl.add_argument("--concurrency", type=int, default=2, help="concurrent requests per host")
    crawl.add_argument("--max-pages", type=int, default=5000, help="safety stop per host")
    crawl.add_argument("--depth", type=int, default=6, help="maximum link depth")
    crawl.set_defaults(func=cmd_crawl)

    triage = sub.add_parser("triage", help="run deterministic checks on downloaded PDFs")
    triage.add_argument("--db", default="data/adascan.db")
    triage.add_argument("--run", type=int, help="run id (default: latest)")
    triage.set_defaults(func=cmd_triage)

    report = sub.add_parser("report", help="generate an audit report")
    report.add_argument("--db", default="data/adascan.db")
    report.add_argument("--run", type=int, help="run id (default: latest)")
    report.add_argument("--out", default="data/reports")
    report.add_argument("--entity", default="", help="entity name for the report header")
    report.add_argument(
        "--large-entity",
        action="store_true",
        help="entity serves 50,000+ people (April 2027 deadline)",
    )
    report.set_defaults(func=cmd_report)

    runs = sub.add_parser("runs", help="list recent runs")
    runs.add_argument("--db", default="data/adascan.db")
    runs.set_defaults(func=cmd_runs)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    _setup_logging(args.verbose)
    try:
        return int(args.func(args))
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
