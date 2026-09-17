"""Shared fixtures: a local fake government site and sample PDFs."""

from __future__ import annotations

import http.server
import socket
import threading
from pathlib import Path

import pytest

PAGES = {
    "/": b"""<html><head><title>Town of Example</title></head><body>
        <a href="/agendas">Agendas</a>
        <a href="/budget">Budget</a>
        <a href="/private/secret">Private</a>
        <a href="https://other.example.com/away">External</a>
        </body></html>""",
    "/agendas": b"""<html><head><title>Agendas &amp; Minutes</title></head><body>
        <a href="/docs/2026_03_board_agenda.pdf">March agenda</a>
        <a href="/docs/2026_02_board_minutes.pdf">February minutes</a>
        <a href="/calendar?date=2026-01-01">Calendar</a>
        </body></html>""",
    "/budget": b"""<html><head><title>Adopted Budget</title></head><body>
        <a href="/docs/2026_adopted_budget.pdf">2026 budget</a>
        </body></html>""",
    "/private/secret": b"<html><title>Should not be fetched</title></html>",
    "/calendar": b"<html><title>Calendar</title></html>",
}

ROBOTS = b"""User-agent: *
Disallow: /private/
Crawl-delay: 0
"""


def make_pdf(path: Path, pages: int = 2, tagged: bool = False, text: bool = True) -> Path:
    import pikepdf
    import pymupdf

    doc = pymupdf.open()
    for i in range(pages):
        page = doc.new_page()
        if text:
            page.insert_text((72, 72), f"Page {i + 1} of a public meeting record. " * 6)
    doc.save(path)
    doc.close()

    if tagged:
        with pikepdf.open(path, allow_overwriting_input=True) as pdf:
            pdf.Root["/StructTreeRoot"] = pdf.make_indirect(
                pikepdf.Dictionary(Type=pikepdf.Name("/StructTreeRoot"))
            )
            pdf.Root["/Lang"] = pikepdf.String("en-US")
            pdf.save(path)
    return path


class _Handler(http.server.BaseHTTPRequestHandler):
    docs_dir: Path = Path()

    def log_message(self, *args: object) -> None:  # silence test output
        pass

    def do_GET(self) -> None:  # noqa: N802 - stdlib naming
        path = self.path.split("?")[0]

        if path == "/robots.txt":
            self._send(200, "text/plain", ROBOTS)
            return
        if path.startswith("/docs/"):
            target = self.docs_dir / Path(path).name
            if target.exists():
                self._send(200, "application/pdf", target.read_bytes())
            else:
                self._send(404, "text/plain", b"missing")
            return
        if path in PAGES:
            self._send(200, "text/html", PAGES[path])
            return
        self._send(404, "text/html", b"<html><title>404</title></html>")

    def _send(self, code: int, content_type: str, body: bytes) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Last-Modified", "Wed, 01 Apr 2026 12:00:00 GMT")
        self.end_headers()
        self.wfile.write(body)


@pytest.fixture(scope="session")
def docs_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    d = tmp_path_factory.mktemp("docs")
    make_pdf(d / "2026_03_board_agenda.pdf", pages=3, tagged=False)
    make_pdf(d / "2026_02_board_minutes.pdf", pages=5, tagged=True)
    make_pdf(d / "2026_adopted_budget.pdf", pages=60, tagged=False)
    return d


@pytest.fixture(scope="session")
def site(docs_dir: Path):
    """Serve the fake site on a free port for the whole session."""
    _Handler.docs_dir = docs_dir
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]

    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()
    server.server_close()
