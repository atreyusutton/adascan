"""URL normalization, scope and trap detection."""

from __future__ import annotations

import pytest

from adascan import urls as u


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("HTTPS://WWW.Example.GOV/a/#frag", "https://www.example.gov/a"),
        ("https://x.gov:443/a", "https://x.gov/a"),
        ("http://x.gov:80/a", "http://x.gov/a"),
        ("https://x.gov/a?b=2&a=1", "https://x.gov/a?a=1&b=2"),
        ("https://x.gov", "https://x.gov/"),
        ("https://x.gov/a/b/", "https://x.gov/a/b"),
    ],
)
def test_normalize(raw, expected):
    assert u.normalize(raw) == expected


@pytest.mark.parametrize(
    "host,expected",
    [
        ("www.castlerock.gov", "castlerock.gov"),
        ("docs.town.castlerock.gov", "castlerock.gov"),
        ("meetings.fire.co.us", "fire.co.us"),
        ("example.org", "example.org"),
    ],
)
def test_registrable_domain(host, expected):
    assert u.registrable_domain(host) == expected


def test_scope_follows_subdomains_but_not_strangers():
    assert u.same_scope("https://docs.castlerock.gov/x", "castlerock.gov")
    assert not u.same_scope("https://evil.com/x", "castlerock.gov")


@pytest.mark.parametrize(
    "url,expected",
    [
        ("/a/minutes.PDF", True),
        ("/a/minutes.pdf?v=2", True),
        ("/a/page", False),
        ("/a/sheet.xlsx", False),
    ],
)
def test_is_pdf(url, expected):
    assert u.is_pdf(url) is expected


def test_document_detection_covers_office_formats():
    assert u.is_document("/x/report.docx")
    assert u.is_document("/x/budget.xlsx")
    assert not u.is_document("/x/index.html")


def test_calendar_traps_are_detected_only_after_a_threshold():
    counts = {"/calendar": 5}
    assert not u.looks_like_trap("https://x.gov/calendar?date=2026-01-01", counts)
    counts["/calendar"] = 250
    assert u.looks_like_trap("https://x.gov/calendar?date=2026-01-01", counts)
    # A trap-shaped path without a trap parameter is left alone.
    assert not u.looks_like_trap("https://x.gov/calendar", counts)


@pytest.mark.parametrize("host", ["127.0.0.1", "10.0.0.5", "::1"])
def test_ip_literals_have_no_registrable_domain(host):
    # A crawl of 127.0.0.1 must not report its domain as "0.1".
    assert u.registrable_domain(host) == host
