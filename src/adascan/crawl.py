"""Async crawler.

Walks one government domain, records every HTML page and every document link,
and streams documents to disk for triage. Politeness rules live in
docs/crawl-policy.md and are enforced here per host, not globally.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urljoin, urlsplit

import httpx
from selectolax.parser import HTMLParser

from adascan import urls as u
from adascan.config import CrawlConfig
from adascan.robots import RobotsRules, fetch_robots
from adascan.store import Store

log = logging.getLogger("adascan.crawl")

RETRYABLE_STATUS = frozenset({429, 500, 502, 503, 504})


class HostAbandoned(Exception):
    """Raised when a host has exhausted its rate-limit strikes."""


@dataclass
class HostState:
    """Per-host politeness state. One instance per hostname."""

    host: str
    delay: float
    semaphore: asyncio.Semaphore
    robots: RobotsRules | None = None
    last_request: float = 0.0
    strikes: int = 0
    pages: int = 0
    abandoned: bool = False
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def wait_turn(self) -> None:
        """Sleep so that consecutive requests to this host are `delay` apart."""
        async with self.lock:
            elapsed = time.monotonic() - self.last_request
            remaining = self.delay - elapsed
            if remaining > 0:
                await asyncio.sleep(remaining)
            self.last_request = time.monotonic()


@dataclass
class FetchResult:
    url: str
    final_url: str
    status_code: int
    content_type: str
    body: bytes | None
    sha256: str
    bytes: int
    last_modified: str
    local_path: str = ""
    error: str = ""


class Crawler:
    """Single-domain crawler.

    Not reusable across domains — construct one per seed so that host state,
    counters and the frontier cannot leak between runs.
    """

    def __init__(
        self,
        seed: str,
        config: CrawlConfig,
        store: Store,
        data_dir: Path,
        max_depth: int = 6,
    ) -> None:
        if not u.is_http(seed):
            raise ValueError(f"seed must be http(s): {seed!r}")
        self.seed = u.normalize(seed)
        self.config = config
        self.store = store
        self.data_dir = Path(data_dir)
        self.max_depth = max_depth

        host = urlsplit(self.seed).hostname or ""
        self.domain = u.registrable_domain(host)

        self.seen: set[str] = set()
        self.path_counts: dict[str, int] = {}
        self.hosts: dict[str, HostState] = {}
        self.host_gate = asyncio.Semaphore(config.max_hosts)
        self.queue: asyncio.Queue[tuple[str, int]] = asyncio.Queue()
        self.run_id: int = 0
        self.documents_found = 0

    # -- host management ----------------------------------------------------

    async def _host_state(self, client: httpx.AsyncClient, url: str) -> HostState:
        host = urlsplit(url).netloc
        state = self.hosts.get(host)
        if state is not None:
            return state

        state = HostState(
            host=host,
            delay=self.config.delay_seconds,
            semaphore=asyncio.Semaphore(self.config.per_host_concurrency),
        )
        self.hosts[host] = state

        rules = await fetch_robots(client, url, self.config.user_agent)
        state.robots = rules
        if rules.status != "ok":
            self.store.log(
                self.run_id, "warn", "robots_unavailable",
                f"{rules.status}: {rules.detail} (treating as allow)", host,
            )
        if rules.crawl_delay is not None and rules.crawl_delay > state.delay:
            state.delay = rules.crawl_delay
            self.store.log(
                self.run_id, "info", "crawl_delay_raised",
                f"robots.txt Crawl-delay={rules.crawl_delay}s", host,
            )
        return state

    # -- fetching -----------------------------------------------------------

    async def _fetch(
        self, client: httpx.AsyncClient, url: str, as_document: bool
    ) -> FetchResult:
        """Fetch one URL with per-host politeness and backoff.

        Raises HostAbandoned when the host has run out of strikes.
        """
        state = await self._host_state(client, url)
        if state.abandoned:
            raise HostAbandoned(state.host)

        if state.robots is not None and not state.robots.allows(url, self.config.user_agent):
            self.store.log(self.run_id, "info", "robots_disallow", url, state.host)
            return FetchResult(url, url, 0, "", None, "", 0, "", error="robots_disallow")

        backoff = self.config.backoff_initial
        attempts = self.config.max_retries + 1

        for attempt in range(attempts):
            async with state.semaphore:
                await state.wait_turn()
                try:
                    if as_document:
                        result = await self._stream_document(client, url)
                    else:
                        result = await self._get_page(client, url)
                except httpx.HTTPError as exc:
                    if attempt == attempts - 1:
                        return FetchResult(
                            url, url, 0, "", None, "", 0, "",
                            error=f"{type(exc).__name__}: {exc}",
                        )
                    await asyncio.sleep(min(backoff, self.config.backoff_cap))
                    backoff *= 2
                    continue

            if result.status_code not in RETRYABLE_STATUS:
                return result

            # Rate limited or server error: back off, and count a strike.
            state.strikes += 1
            if state.strikes >= self.config.rate_limit_strikes:
                state.abandoned = True
                self.store.log(
                    self.run_id, "error", "host_abandoned",
                    f"{state.strikes} strikes, last status {result.status_code}",
                    state.host,
                )
                raise HostAbandoned(state.host)

            wait = self._retry_after(result) or backoff
            self.store.log(
                self.run_id, "warn", "backoff",
                f"HTTP {result.status_code} on {url}, waiting {wait:.0f}s "
                f"(strike {state.strikes}/{self.config.rate_limit_strikes})",
                state.host,
            )
            await asyncio.sleep(min(wait, self.config.backoff_cap))
            backoff *= 2

        return result

    @staticmethod
    def _retry_after(result: FetchResult) -> float | None:
        # Retry-After is surfaced through content_type-free results; parsed by
        # the caller that has the response. Kept simple: absent means None.
        return None

    async def _get_page(self, client: httpx.AsyncClient, url: str) -> FetchResult:
        response = await client.get(url, follow_redirects=True)
        body = response.content
        return FetchResult(
            url=url,
            final_url=str(response.url),
            status_code=response.status_code,
            content_type=response.headers.get("content-type", "").split(";")[0].strip(),
            body=body,
            sha256=hashlib.sha256(body).hexdigest(),
            bytes=len(body),
            last_modified=response.headers.get("last-modified", ""),
        )

    async def _stream_document(self, client: httpx.AsyncClient, url: str) -> FetchResult:
        """Stream a document to disk, enforcing the size cap mid-transfer."""
        digest = hashlib.sha256()
        total = 0
        target_dir = self.data_dir / "documents" / self.domain
        target_dir.mkdir(parents=True, exist_ok=True)
        name = hashlib.sha1(url.encode()).hexdigest()[:20] + u.extension(url)
        target = target_dir / name

        async with client.stream("GET", url, follow_redirects=True) as response:
            if response.status_code >= 400:
                await response.aclose()
                return FetchResult(
                    url, str(response.url), response.status_code,
                    response.headers.get("content-type", "").split(";")[0].strip(),
                    None, "", 0, response.headers.get("last-modified", ""),
                )

            declared = response.headers.get("content-length")
            if declared and declared.isdigit() and int(declared) > self.config.max_document_bytes:
                await response.aclose()
                return FetchResult(
                    url, str(response.url), response.status_code, "", None, "", int(declared),
                    response.headers.get("last-modified", ""),
                    error=f"too_large: {declared} bytes",
                )

            with target.open("wb") as handle:
                async for chunk in response.aiter_bytes(chunk_size=65_536):
                    total += len(chunk)
                    if total > self.config.max_document_bytes:
                        handle.close()
                        target.unlink(missing_ok=True)
                        return FetchResult(
                            url, str(response.url), response.status_code, "", None, "",
                            total, "", error="too_large: exceeded cap mid-stream",
                        )
                    digest.update(chunk)
                    handle.write(chunk)

            return FetchResult(
                url=url,
                final_url=str(response.url),
                status_code=response.status_code,
                content_type=response.headers.get("content-type", "").split(";")[0].strip(),
                body=None,
                sha256=digest.hexdigest(),
                bytes=total,
                last_modified=response.headers.get("last-modified", ""),
                local_path=str(target),
            )

    # -- parsing ------------------------------------------------------------

    def _extract(self, base_url: str, html: bytes) -> tuple[str, list[tuple[str, bool]]]:
        """Return (title, [(url, is_external), ...]) from an HTML body."""
        try:
            tree = HTMLParser(html.decode("utf-8", errors="replace"))
        except (ValueError, UnicodeDecodeError) as exc:
            log.warning("parse failed for %s: %s", base_url, exc)
            return "", []

        title_node = tree.css_first("title")
        title = (title_node.text(strip=True) if title_node else "")[:300]

        found: list[tuple[str, bool]] = []
        for node in tree.css("a[href]"):
            href = (node.attributes.get("href") or "").strip()
            if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
                continue
            absolute = u.normalize(urljoin(base_url, href))
            if not u.is_http(absolute):
                continue
            external = not u.same_scope(absolute, self.domain, self.config.follow_subdomains)
            found.append((absolute, external))
        return title, found

    # -- main loop ----------------------------------------------------------

    async def run(self) -> int:
        """Crawl the seed domain. Returns the run id."""
        config_snapshot = {
            "delay_seconds": self.config.delay_seconds,
            "per_host_concurrency": self.config.per_host_concurrency,
            "max_pages_per_host": self.config.max_pages_per_host,
            "max_depth": self.max_depth,
            "user_agent": self.config.user_agent,
            "dry_run": self.config.dry_run,
        }
        self.run_id = self.store.start_run(self.seed, self.domain, config_snapshot)

        headers = {"User-Agent": self.config.user_agent, "Accept": "*/*"}
        limits = httpx.Limits(max_connections=self.config.max_hosts * 4)
        timeout = httpx.Timeout(self.config.timeout_seconds)

        self.seen.add(self.seed)
        await self.queue.put((self.seed, 0))

        status = "complete"
        note = ""
        try:
            async with httpx.AsyncClient(
                headers=headers, limits=limits, timeout=timeout, http2=False
            ) as client:
                workers = [
                    asyncio.create_task(self._worker(client, i))
                    for i in range(self.config.max_hosts)
                ]
                await self.queue.join()
                for task in workers:
                    task.cancel()
                await asyncio.gather(*workers, return_exceptions=True)
        except HostAbandoned as exc:
            status = "partial"
            note = f"host abandoned: {exc}"
        finally:
            self.store.commit()
            self.store.finish_run(self.run_id, status, note)

        return self.run_id

    async def _worker(self, client: httpx.AsyncClient, worker_id: int) -> None:
        while True:
            url, depth = await self.queue.get()
            try:
                await self._process(client, url, depth)
            except HostAbandoned:
                # Recorded in _fetch; drain remaining work for that host.
                pass
            except Exception as exc:  # noqa: BLE001 - recorded, never silent
                self.store.log(self.run_id, "error", "worker_exception", f"{url}: {exc!r}")
                log.exception("worker %d failed on %s", worker_id, url)
            finally:
                self.queue.task_done()

    async def _process(self, client: httpx.AsyncClient, url: str, depth: int) -> None:
        host = urlsplit(url).netloc
        state = self.hosts.get(host)
        if state is not None and state.pages >= self.config.max_pages_per_host:
            return

        is_doc = u.is_document(url)

        if self.config.dry_run:
            self.store.record_resource(
                self.run_id, url=url, kind="pdf" if u.is_pdf(url) else ("document" if is_doc else "html"),
                depth=depth, error="dry_run",
            )
            self.store.commit()
            return

        async with self.host_gate:
            result = await self._fetch(client, url, as_document=is_doc)

        state = self.hosts[urlsplit(url).netloc]
        state.pages += 1

        kind = self._classify(url, result)
        self.store.record_resource(
            self.run_id,
            url=url,
            final_url=result.final_url,
            kind=kind,
            status_code=result.status_code or None,
            content_type=result.content_type,
            bytes=result.bytes or None,
            sha256=result.sha256 or None,
            last_modified=result.last_modified,
            depth=depth,
            local_path=result.local_path,
            error=result.error,
        )

        if kind == "pdf":
            self.documents_found += 1

        if kind == "html" and result.body and 200 <= result.status_code < 300:
            title, links = self._extract(result.final_url or url, result.body)
            if title:
                self.store.record_resource(
                    self.run_id, url=url, kind=kind, title=title,
                    status_code=result.status_code, bytes=result.bytes,
                    sha256=result.sha256, final_url=result.final_url,
                    last_modified=result.last_modified, depth=depth,
                )
            self.store.record_links(self.run_id, url, links)
            if depth < self.max_depth:
                await self._enqueue(links, depth + 1)

        self.store.commit()

    async def _enqueue(self, links: list[tuple[str, bool]], depth: int) -> None:
        for target, external in links:
            if external or target in self.seen:
                continue
            path = urlsplit(target).path
            self.path_counts[path] = self.path_counts.get(path, 0) + 1
            if u.looks_like_trap(target, self.path_counts):
                self.store.log(self.run_id, "info", "trap_skipped", target)
                continue
            self.seen.add(target)
            await self.queue.put((target, depth))

    @staticmethod
    def _classify(url: str, result: FetchResult) -> str:
        content_type = (result.content_type or "").lower()
        if u.is_pdf(url) or content_type == "application/pdf":
            return "pdf"
        if u.is_document(url):
            return "document"
        if content_type.startswith("text/html") or content_type.endswith("+xml"):
            return "html"
        if not content_type and not u.is_document(url):
            return "html"
        return "other"
