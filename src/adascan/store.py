"""SQLite inventory store.

Week-one choice, deliberately not Postgres. A scan run is single-operator and
single-machine, and a file you can copy and diff is the right shape while the
schema is still moving. The customer-facing app is Neon Postgres per
docs/architecture.md; migrating this table set is a known, small job.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id          INTEGER PRIMARY KEY,
    seed        TEXT NOT NULL,
    domain      TEXT NOT NULL,
    started_at  TEXT NOT NULL,
    finished_at TEXT,
    status      TEXT NOT NULL DEFAULT 'running',
    config      TEXT NOT NULL,
    note        TEXT
);

CREATE TABLE IF NOT EXISTS resources (
    id            INTEGER PRIMARY KEY,
    run_id        INTEGER NOT NULL REFERENCES runs(id),
    url           TEXT NOT NULL,
    final_url     TEXT,
    kind          TEXT NOT NULL,          -- html | pdf | document | other
    status_code   INTEGER,
    content_type  TEXT,
    bytes         INTEGER,
    sha256        TEXT,
    last_modified TEXT,
    title         TEXT,
    depth         INTEGER NOT NULL DEFAULT 0,
    fetched_at    TEXT,
    local_path    TEXT,
    error         TEXT,
    UNIQUE (run_id, url)
);

CREATE INDEX IF NOT EXISTS idx_resources_run_kind ON resources (run_id, kind);
CREATE INDEX IF NOT EXISTS idx_resources_sha      ON resources (run_id, sha256);

CREATE TABLE IF NOT EXISTS links (
    run_id   INTEGER NOT NULL REFERENCES runs(id),
    src      TEXT NOT NULL,
    dst      TEXT NOT NULL,
    external INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_links_run ON links (run_id, dst);

CREATE TABLE IF NOT EXISTS pdf_triage (
    run_id        INTEGER NOT NULL REFERENCES runs(id),
    url           TEXT NOT NULL,
    pages         INTEGER,
    tagged        INTEGER,               -- 1 = StructTreeRoot present
    has_text      INTEGER,               -- 1 = extractable text layer
    scanned       INTEGER,               -- 1 = image-only, needs OCR
    images        INTEGER,
    table_regions INTEGER,
    form_fields   INTEGER,
    linearized    INTEGER,
    has_lang      INTEGER,
    has_title     INTEGER,
    doc_type      TEXT,
    complexity    TEXT,                  -- easy | moderate | hard | decline
    error         TEXT,
    UNIQUE (run_id, url)
);

CREATE TABLE IF NOT EXISTS events (
    run_id     INTEGER NOT NULL REFERENCES runs(id),
    at         TEXT NOT NULL,
    host       TEXT,
    level      TEXT NOT NULL,           -- info | warn | error
    event      TEXT NOT NULL,
    detail     TEXT
);
"""


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Store:
    """Thin wrapper over SQLite. Synchronous by design — writes are cheap
    relative to network waits, and one writer avoids lock contention."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        with closing(self.conn.cursor()) as cur:
            cur.executescript(SCHEMA)
        self.conn.commit()

    def close(self) -> None:
        self.conn.commit()
        self.conn.close()

    def __enter__(self) -> "Store":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    # -- runs ---------------------------------------------------------------

    def start_run(self, seed: str, domain: str, config: dict[str, Any]) -> int:
        cur = self.conn.execute(
            "INSERT INTO runs (seed, domain, started_at, config) VALUES (?,?,?,?)",
            (seed, domain, utcnow(), json.dumps(config, sort_keys=True)),
        )
        self.conn.commit()
        run_id = cur.lastrowid
        if run_id is None:
            raise RuntimeError("SQLite did not return a run id")
        return run_id

    def finish_run(self, run_id: int, status: str, note: str = "") -> None:
        self.conn.execute(
            "UPDATE runs SET finished_at=?, status=?, note=? WHERE id=?",
            (utcnow(), status, note, run_id),
        )
        self.conn.commit()

    # -- resources ----------------------------------------------------------

    def record_resource(self, run_id: int, **fields: Any) -> None:
        fields["run_id"] = run_id
        fields.setdefault("fetched_at", utcnow())
        columns = ", ".join(fields)
        placeholders = ", ".join("?" for _ in fields)
        self.conn.execute(
            f"INSERT OR REPLACE INTO resources ({columns}) VALUES ({placeholders})",
            tuple(fields.values()),
        )

    def record_links(self, run_id: int, src: str, targets: list[tuple[str, bool]]) -> None:
        self.conn.executemany(
            "INSERT INTO links (run_id, src, dst, external) VALUES (?,?,?,?)",
            [(run_id, src, dst, int(external)) for dst, external in targets],
        )

    def record_triage(self, run_id: int, url: str, **fields: Any) -> None:
        fields["run_id"] = run_id
        fields["url"] = url
        columns = ", ".join(fields)
        placeholders = ", ".join("?" for _ in fields)
        self.conn.execute(
            f"INSERT OR REPLACE INTO pdf_triage ({columns}) VALUES ({placeholders})",
            tuple(fields.values()),
        )

    def log(self, run_id: int, level: str, event: str, detail: str = "", host: str = "") -> None:
        self.conn.execute(
            "INSERT INTO events (run_id, at, host, level, event, detail) VALUES (?,?,?,?,?,?)",
            (run_id, utcnow(), host, level, event, detail),
        )
        self.conn.commit()

    def commit(self) -> None:
        self.conn.commit()

    # -- reads --------------------------------------------------------------

    def resources(self, run_id: int, kind: str | None = None) -> Iterator[sqlite3.Row]:
        if kind:
            yield from self.conn.execute(
                "SELECT * FROM resources WHERE run_id=? AND kind=? ORDER BY url",
                (run_id, kind),
            )
        else:
            yield from self.conn.execute(
                "SELECT * FROM resources WHERE run_id=? ORDER BY url", (run_id,)
            )

    def counts(self, run_id: int) -> dict[str, int]:
        rows = self.conn.execute(
            "SELECT kind, COUNT(*) AS n FROM resources WHERE run_id=? GROUP BY kind",
            (run_id,),
        )
        return {row["kind"]: row["n"] for row in rows}

    def run(self, run_id: int) -> sqlite3.Row | None:
        return self.conn.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()

    def latest_run(self) -> sqlite3.Row | None:
        return self.conn.execute(
            "SELECT * FROM runs ORDER BY id DESC LIMIT 1"
        ).fetchone()
