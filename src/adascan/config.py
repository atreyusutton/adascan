"""Crawl configuration.

Defaults encode `docs/crawl-policy.md`. Changing a default here changes the
policy; update that document in the same commit.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

USER_AGENT_TEMPLATE = (
    "adascan/{version} (+https://github.com/atreyusutton/adascan; contact: {contact})"
)

# Extensions we treat as documents worth inventorying rather than pages to walk.
DOCUMENT_EXTENSIONS = frozenset(
    {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".rtf"}
)

# Query parameters that produce infinite calendar/pagination surfaces.
TRAP_PARAMS = frozenset({"date", "month", "year", "cal_date", "page", "start", "from"})


class ConfigError(Exception):
    """Raised when the crawler is misconfigured and must not start."""


@dataclass(frozen=True)
class CrawlConfig:
    """Operational limits for a crawl run.

    Every field maps to a row in docs/crawl-policy.md.
    """

    contact: str
    delay_seconds: float = 1.0
    per_host_concurrency: int = 2
    max_hosts: int = 8
    timeout_seconds: float = 30.0
    max_pages_per_host: int = 5_000
    max_document_bytes: int = 150 * 1024 * 1024
    max_retries: int = 2
    backoff_initial: float = 5.0
    backoff_cap: float = 120.0
    rate_limit_strikes: int = 3
    follow_subdomains: bool = True
    dry_run: bool = False
    user_agent: str = field(init=False)

    def __post_init__(self) -> None:
        from adascan import __version__

        ua = USER_AGENT_TEMPLATE.format(version=__version__, contact=self.contact)
        object.__setattr__(self, "user_agent", ua)

    @classmethod
    def from_env(cls, **overrides: object) -> CrawlConfig:
        """Build config from the environment.

        Refuses to construct without ADASCAN_CONTACT. An anonymous crawler
        hitting hundreds of .gov domains is indistinguishable from
        reconnaissance, so this is a hard failure rather than a warning.
        """
        contact = os.environ.get("ADASCAN_CONTACT", "").strip()
        if not contact:
            raise ConfigError(
                "ADASCAN_CONTACT is not set. Set it to a real contact address "
                "before crawling any external host — see docs/crawl-policy.md."
            )
        if "@" not in contact and not contact.startswith("http"):
            raise ConfigError(
                f"ADASCAN_CONTACT={contact!r} is not an email address or URL."
            )

        dry_run = os.environ.get("ADASCAN_DRY_RUN", "") not in ("", "0", "false")
        return cls(contact=contact, dry_run=dry_run, **overrides)  # type: ignore[arg-type]
