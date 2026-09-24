"""Inspect one local PDF with the optional pypdf dependency."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PDF = PROJECT_ROOT / "data" / "fixtures" / "exploration-sample.pdf"
DEFAULT_OUTPUT = (
    PROJECT_ROOT / "data" / "generated" / "pdf_exploration" / "inspect_output.txt"
)


class InspectionError(RuntimeError):
    """Raised when a PDF cannot be inspected safely."""


def _metadata_value(metadata: Any, key: str) -> str | None:
    """Return a normalized metadata value from pypdf's mapping-like object."""
    if metadata is None:
        return None
    value = metadata.get(key)
    return str(value).strip() if value else None


def inspect_pdf(path: Path) -> tuple[dict[str, str | int | None], str]:
    """Return basic metadata and first-page text from a local PDF."""
    if not path.is_file():
        raise InspectionError(f"PDF file does not exist: {path}")
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise InspectionError(
            'pypdf is not installed; install the optional group with pip install -e ".[exploration]"'
        ) from exc

    try:
        reader = PdfReader(path)
        metadata = reader.metadata
        page_count = len(reader.pages)
        first_page_text = reader.pages[0].extract_text() if page_count else ""
    except Exception as exc:  # library exception types differ between releases
        raise InspectionError(f"cannot read PDF {path}: {exc}") from exc

    details: dict[str, str | int | None] = {
        "pages": page_count,
        "author": _metadata_value(metadata, "/Author"),
        "title": _metadata_value(metadata, "/Title"),
    }
    return details, first_page_text or ""


def write_text_output(path: Path, text: str) -> None:
    """Write extracted text to the deterministic exploration location."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    """Run the PDF inspection command."""
    parser = argparse.ArgumentParser(description="Inspect a local PDF report")
    parser.add_argument("pdf", nargs="?", type=Path, default=DEFAULT_PDF)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)

    try:
        details, text = inspect_pdf(args.pdf)
        write_text_output(args.output, text)
    except (InspectionError, OSError) as exc:
        print(f"pdf inspection failed: {exc}", file=sys.stderr)
        return 1

    print(f"PDF: {args.pdf}")
    print(f"Pages: {details['pages']}")
    print(f"Author: {details['author'] or '-'}")
    print(f"Title: {details['title'] or '-'}")
    print(f"First-page text: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
