"""URL normalization and scope rules."""

from __future__ import annotations

from urllib.parse import parse_qsl, urldefrag, urlencode, urlsplit, urlunsplit

import re

from adascan.config import DOCUMENT_EXTENSIONS, TRAP_PARAMS

_IPV4 = re.compile(r"\d{1,3}(?:\.\d{1,3}){3}")

# Suffixes where the registrable domain is one label deeper than usual.
# Government sites hit this constantly: e.g. `ci.foo.co.us`.
_MULTI_LABEL_SUFFIXES = ("co.us", "k12.*.us", "cog.*.us")


def normalize(url: str) -> str:
    """Canonicalize a URL for deduplication.

    Lowercases scheme and host, drops the fragment, removes default ports,
    sorts query parameters, and strips a trailing slash from non-root paths.
    Does not attempt to resolve redirects — that is the fetcher's job.
    """
    url, _ = urldefrag(url.strip())
    parts = urlsplit(url)

    scheme = parts.scheme.lower()
    host = parts.hostname or ""
    host = host.lower().rstrip(".")

    netloc = host
    if parts.port and not (
        (scheme == "http" and parts.port == 80) or (scheme == "https" and parts.port == 443)
    ):
        netloc = f"{host}:{parts.port}"

    path = parts.path or "/"
    if len(path) > 1 and path.endswith("/"):
        path = path.rstrip("/")

    query = urlencode(sorted(parse_qsl(parts.query, keep_blank_values=True)))

    return urlunsplit((scheme, netloc, path, query, ""))


def registrable_domain(host: str) -> str:
    """Best-effort registrable domain.

    Deliberately heuristic — a full PSL dependency is not worth it for the
    `.gov`, `.us` and `.org` hosts this crawler sees. Errs toward a *broader*
    match, which keeps subdomains of one entity together.
    """
    host = host.lower().rstrip(".")

    # IP literals have no registrable domain — return them whole, or a crawl of
    # 127.0.0.1 reports its domain as "0.1".
    if _IPV4.fullmatch(host) or ":" in host:
        return host

    labels = host.split(".")
    if len(labels) <= 2:
        return host

    # `something.co.us`, `school.k12.co.us` — keep three labels.
    if labels[-1] == "us" and len(labels) >= 3 and len(labels[-2]) <= 4:
        return ".".join(labels[-3:]) if len(labels) >= 3 else host

    return ".".join(labels[-2:])


def same_scope(url: str, seed_domain: str, follow_subdomains: bool = True) -> bool:
    """Is `url` inside the crawl scope defined by `seed_domain`?"""
    host = urlsplit(url).hostname
    if not host:
        return False
    host = host.lower()
    if follow_subdomains:
        return registrable_domain(host) == seed_domain
    return host == seed_domain


def is_document(url: str) -> bool:
    """Does this URL look like a document rather than a page to walk?"""
    return extension(url) in DOCUMENT_EXTENSIONS


def is_pdf(url: str) -> bool:
    return extension(url) == ".pdf"


def extension(url: str) -> str:
    path = urlsplit(url).path
    dot = path.rfind(".")
    slash = path.rfind("/")
    if dot == -1 or dot < slash:
        return ""
    return path[dot:].lower()


def looks_like_trap(url: str, seen_path_counts: dict[str, int], threshold: int = 200) -> bool:
    """Heuristic guard against calendar and pagination traps.

    A path we have already visited 200+ times with only query variation is a
    generated surface, not content. Recorded rather than silently skipped —
    see the caller.
    """
    parts = urlsplit(url)
    if not parts.query:
        return False
    params = {k.lower() for k, _ in parse_qsl(parts.query, keep_blank_values=True)}
    if not params & TRAP_PARAMS:
        return False
    return seen_path_counts.get(parts.path, 0) >= threshold


def is_http(url: str) -> bool:
    return urlsplit(url).scheme in ("http", "https")
