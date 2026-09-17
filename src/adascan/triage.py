"""Deterministic PDF triage.

Cheap structural checks only — no models, no tokens. Per docs/architecture.md
this stage decides routing, and routing is where margin is won or lost:
misrouting one 400-page board packet into the easy path costs more than a
hundred correctly routed documents earned.

Nothing here judges *quality*. A PDF can be tagged and still be unusable. That
judgment belongs to the pipeline and the eval harness, not to triage.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path

try:
    import pikepdf

    HAVE_PIKEPDF = True
except ImportError:  # pragma: no cover - optional dependency
    HAVE_PIKEPDF = False

try:
    # The `fitz` alias is deprecated upstream; prefer the real package name.
    import pymupdf as fitz

    HAVE_FITZ = True
except ImportError:  # pragma: no cover - optional dependency
    try:
        import fitz

        HAVE_FITZ = True
    except ImportError:
        HAVE_FITZ = False


class TriageUnavailable(Exception):
    """Raised when PDF libraries are not installed."""


# Filename and title patterns, ordered — first match wins.
DOC_TYPE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("agenda", re.compile(r"\bagenda", re.I)),
    ("minutes", re.compile(r"\bminutes?\b", re.I)),
    ("budget", re.compile(r"\bbudget|appropriat|audit|financial|cafr\b", re.I)),
    ("resolution", re.compile(r"\bresolution|ordinance|proclamation\b", re.I)),
    ("map", re.compile(r"\bmap|zoning|plat|exhibit|drawing\b", re.I)),
    ("form", re.compile(r"\bform|application|permit|licen[cs]e\b", re.I)),
    ("newsletter", re.compile(r"\bnewsletter|bulletin|gazette\b", re.I)),
    ("notice", re.compile(r"\bnotice|hearing|posting\b", re.I)),
)

# Text-layer density below this is treated as a scan with stray OCR artifacts.
MIN_CHARS_PER_PAGE = 50


@dataclass
class TriageResult:
    pages: int | None = None
    tagged: int | None = None
    has_text: int | None = None
    scanned: int | None = None
    images: int | None = None
    table_regions: int | None = None
    form_fields: int | None = None
    linearized: int | None = None
    has_lang: int | None = None
    has_title: int | None = None
    doc_type: str = "unknown"
    complexity: str = "unknown"
    error: str = ""

    def as_row(self) -> dict[str, object]:
        return asdict(self)


# Government filenames separate words with underscores, hyphens and dots, and
# `\b` does not match between `_` and a letter — so separators are normalized
# to spaces before matching. `2025_adopted_budget.pdf` must hit "budget".
_SEPARATORS = re.compile(r"[_\-.+%]+")


def guess_doc_type(url: str, title: str = "") -> str:
    """Classify by filename and title. Deliberately crude — a wrong guess costs
    a routing decision, not a document, and the eval harness reports by type so
    a systematically bad guess shows up as a bad cohort."""
    haystack = _SEPARATORS.sub(" ", f"{url} {title}")
    for name, pattern in DOC_TYPE_PATTERNS:
        if pattern.search(haystack):
            return name
    return "unknown"


def classify_complexity(result: TriageResult) -> str:
    """Route to a processing tier.

    Errs pessimistic: anything with a real chance of needing a human lands in
    `hard` or `decline` rather than `easy`. Over-routing to `hard` costs review
    minutes; under-routing costs a bad deliverable.
    """
    if result.error:
        return "decline"
    if result.scanned:
        # OCR errors propagate into tags — priced separately or declined.
        return "decline"
    if result.form_fields:
        return "decline"
    pages = result.pages or 0
    if result.doc_type == "map":
        return "decline"
    if pages > 200:
        return "hard"
    if result.doc_type == "budget" or (result.table_regions or 0) > 8:
        return "hard"
    if pages > 40 or (result.table_regions or 0) > 2:
        return "moderate"
    if result.doc_type in ("agenda", "minutes", "notice") and pages <= 40:
        return "easy"
    return "moderate"


def triage_pdf(path: Path | str, url: str = "", title: str = "") -> TriageResult:
    """Run deterministic checks on one PDF.

    Never raises for a malformed document — a file we cannot open is a real
    finding (government PDFs are frequently broken) and is recorded as
    `decline` with the reason.
    """
    if not (HAVE_PIKEPDF and HAVE_FITZ):
        raise TriageUnavailable(
            "PDF triage needs pikepdf and pymupdf: pip install 'adascan[pdf]'"
        )

    path = Path(path)
    result = TriageResult(doc_type=guess_doc_type(url or path.name, title))

    if not path.exists():
        result.error = "missing_file"
        result.complexity = "decline"
        return result

    try:
        with pikepdf.open(path) as pdf:
            root = pdf.Root
            result.pages = len(pdf.pages)
            result.tagged = int("/StructTreeRoot" in root)
            result.has_lang = int("/Lang" in root and bool(str(root.get("/Lang", ""))))
            result.linearized = int(getattr(pdf, "is_linearized", False))

            acroform = root.get("/AcroForm")
            field_count = 0
            if acroform is not None:
                fields = acroform.get("/Fields")
                if fields is not None:
                    field_count = len(fields)
            result.form_fields = field_count

            with pdf.open_metadata() as meta:
                title_value = meta.get("dc:title") or ""
            result.has_title = int(bool(str(title_value).strip()))
    except Exception as exc:  # noqa: BLE001 - malformed PDFs are a finding
        result.error = f"pikepdf: {type(exc).__name__}: {exc}"[:400]
        result.complexity = "decline"
        return result

    try:
        with fitz.open(path) as doc:
            chars = 0
            images = 0
            tables = 0
            sample = min(len(doc), 25)  # cap work on huge packets
            for index in range(sample):
                page = doc[index]
                chars += len(page.get_text("text"))
                images += len(page.get_images(full=False))
                try:
                    tables += len(page.find_tables().tables)
                except (AttributeError, RuntimeError, ValueError):
                    # find_tables is version-dependent; absence is not fatal.
                    pass
            scale = (len(doc) / sample) if sample else 1
            result.images = int(images * scale)
            result.table_regions = int(tables * scale)
            per_page = chars / sample if sample else 0
            result.has_text = int(per_page >= MIN_CHARS_PER_PAGE)
            result.scanned = int(per_page < MIN_CHARS_PER_PAGE and images > 0)
    except Exception as exc:  # noqa: BLE001 - recorded, never silent
        result.error = f"pymupdf: {type(exc).__name__}: {exc}"[:400]
        result.complexity = "decline"
        return result

    result.complexity = classify_complexity(result)
    return result
