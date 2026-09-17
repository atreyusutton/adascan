"""robots.txt fetching and evaluation.

Policy (docs/crawl-policy.md): a disallowed URL is never fetched, including
documents. Crawl-delay raises our delay but never lowers it below the floor.
An unreachable or malformed robots.txt is treated as allow, matching standard
behavior, but the failure is recorded.
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser

import httpx


@dataclass
class RobotsRules:
    """Parsed robots.txt for one host."""

    host: str
    parser: RobotFileParser | None
    crawl_delay: float | None
    status: str  # "ok" | "absent" | "error"
    detail: str = ""

    def allows(self, url: str, user_agent: str) -> bool:
        if self.parser is None:
            return True
        return self.parser.can_fetch(user_agent, url)


def robots_url_for(url: str) -> str:
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, "/robots.txt", "", ""))


async def fetch_robots(
    client: httpx.AsyncClient, url: str, user_agent: str
) -> RobotsRules:
    """Fetch and parse robots.txt for the host of `url`.

    Never raises: a host whose robots.txt cannot be read is still crawlable
    under standard convention, and the caller records the reason.
    """
    host = urlsplit(url).netloc
    target = robots_url_for(url)

    try:
        response = await client.get(target, follow_redirects=True)
    except httpx.HTTPError as exc:
        return RobotsRules(host, None, None, "error", f"{type(exc).__name__}: {exc}")

    if response.status_code == 404:
        return RobotsRules(host, None, None, "absent", "404")
    if response.status_code >= 400:
        return RobotsRules(host, None, None, "error", f"HTTP {response.status_code}")

    parser = RobotFileParser()
    try:
        parser.parse(response.text.splitlines())
    except (ValueError, UnicodeDecodeError) as exc:
        return RobotsRules(host, None, None, "error", f"unparseable: {exc}")

    delay: float | None = None
    try:
        raw_delay = parser.crawl_delay(user_agent)
        if raw_delay is not None:
            delay = float(raw_delay)
    except (ValueError, TypeError):
        delay = None

    return RobotsRules(host, parser, delay, "ok")
