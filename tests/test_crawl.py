"""Integration tests: crawl a real (local) site end to end."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from adascan.config import ConfigError, CrawlConfig
from adascan.crawl import Crawler
from adascan.report import collect, render_markdown
from adascan.store import Store
from adascan.triage import triage_pdf


@pytest.fixture
def config() -> CrawlConfig:
    os.environ["ADASCAN_CONTACT"] = "test@example.com"
    os.environ.pop("ADASCAN_DRY_RUN", None)
    # Zero delay only because the server under test is a local fixture.
    return CrawlConfig.from_env(delay_seconds=0.0, per_host_concurrency=2)


async def test_crawl_inventories_pages_and_pdfs(site, tmp_path, config):
    store = Store(tmp_path / "db.sqlite")
    crawler = Crawler(site, config, store, tmp_path)
    run_id = await crawler.run()

    counts = store.counts(run_id)
    assert counts.get("html", 0) >= 3
    assert counts.get("pdf", 0) == 3

    pdfs = {Path(r["url"]).name for r in store.resources(run_id, "pdf")}
    assert pdfs == {
        "2026_03_board_agenda.pdf",
        "2026_02_board_minutes.pdf",
        "2026_adopted_budget.pdf",
    }

    for row in store.resources(run_id, "pdf"):
        assert row["sha256"], "every fetched document must be hashed"
        assert row["bytes"] > 0
        assert row["last_modified"], "Last-Modified must be recorded"
        assert Path(row["local_path"]).exists()

    store.close()


async def test_robots_disallow_is_respected(site, tmp_path, config):
    store = Store(tmp_path / "db.sqlite")
    crawler = Crawler(site, config, store, tmp_path)
    run_id = await crawler.run()

    disallowed = [
        r for r in store.resources(run_id) if r["url"].endswith("/private/secret")
    ]
    assert disallowed, "the disallowed URL should still be inventoried"
    assert disallowed[0]["error"] == "robots_disallow"
    assert disallowed[0]["status_code"] is None, "it must never have been fetched"
    store.close()


async def test_external_links_recorded_never_fetched(site, tmp_path, config):
    store = Store(tmp_path / "db.sqlite")
    crawler = Crawler(site, config, store, tmp_path)
    run_id = await crawler.run()

    externals = list(
        store.conn.execute(
            "SELECT dst FROM links WHERE run_id=? AND external=1", (run_id,)
        )
    )
    assert any("other.example.com" in row["dst"] for row in externals)

    fetched = [r["url"] for r in store.resources(run_id)]
    assert not any("other.example.com" in url for url in fetched)
    store.close()


async def test_dry_run_issues_no_requests(site, tmp_path, monkeypatch):
    monkeypatch.setenv("ADASCAN_CONTACT", "test@example.com")
    monkeypatch.setenv("ADASCAN_DRY_RUN", "1")
    dry = CrawlConfig.from_env(delay_seconds=0.0)
    assert dry.dry_run

    store = Store(tmp_path / "db.sqlite")
    crawler = Crawler(site, dry, store, tmp_path)
    run_id = await crawler.run()

    rows = list(store.resources(run_id))
    assert rows, "dry run still records the frontier"
    assert all(r["error"] == "dry_run" for r in rows)
    assert all(r["status_code"] is None for r in rows)
    assert not (tmp_path / "documents").exists(), "no documents downloaded"
    store.close()


def test_contact_is_required(monkeypatch):
    monkeypatch.delenv("ADASCAN_CONTACT", raising=False)
    with pytest.raises(ConfigError, match="ADASCAN_CONTACT"):
        CrawlConfig.from_env()


def test_user_agent_carries_contact():
    os.environ["ADASCAN_CONTACT"] = "ops@example.com"
    config = CrawlConfig.from_env()
    assert "ops@example.com" in config.user_agent
    assert config.user_agent.startswith("adascan/")


async def test_triage_and_report_end_to_end(site, tmp_path, config):
    store = Store(tmp_path / "db.sqlite")
    crawler = Crawler(site, config, store, tmp_path)
    run_id = await crawler.run()

    for row in store.resources(run_id, "pdf"):
        result = triage_pdf(row["local_path"], url=row["url"], title=row["title"] or "")
        store.record_triage(run_id, row["url"], **result.as_row())
    store.commit()

    findings = collect(store, run_id)
    assert findings.pdfs_analyzed == 3
    assert findings.total_pdf_pages == 68          # 3 + 5 + 60
    assert findings.untagged == 2                  # minutes was tagged
    assert findings.by_type["agenda"] == 1
    assert findings.by_type["minutes"] == 1
    assert findings.by_type["budget"] == 1
    assert findings.by_complexity["hard"] == 1     # 60-page budget

    low, high = findings.market_rate_range()
    assert (low, high) == (68 * 5.0, 68 * 25.0)

    report = render_markdown(findings, entity_name="Town of Example")
    assert "Town of Example" in report
    assert "$340 – $1,700" in report
    assert "2028-04-26" in report
    # The report must never claim compliance either way.
    assert "does not determine compliance" in report
    assert "is compliant" not in report
    store.close()


async def test_large_entity_gets_the_2027_deadline(site, tmp_path, config):
    store = Store(tmp_path / "db.sqlite")
    crawler = Crawler(site, config, store, tmp_path)
    run_id = await crawler.run()
    findings = collect(store, run_id)

    assert "2027-04-26" in render_markdown(findings, large_entity=True)
    assert "2028-04-26" in render_markdown(findings, large_entity=False)
    store.close()
