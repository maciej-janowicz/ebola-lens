"""Compare optional PDF text extractors on one local file."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
import time
from pathlib import Path
from typing import Callable

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PDF = PROJECT_ROOT / "data" / "fixtures" / "exploration-sample.pdf"
DEFAULT_OUTPUT = (
    PROJECT_ROOT / "data" / "generated" / "pdf_exploration" / "comparison_results.json"
)


def _pypdf_text(path: Path) -> str:
    module = importlib.import_module("pypdf")
    reader = module.PdfReader(path)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _pdfplumber_text(path: Path) -> str:
    module = importlib.import_module("pdfplumber")
    with module.open(path) as document:
        return "\n".join(page.extract_text() or "" for page in document.pages)


def _pymupdf_text(path: Path) -> str:
    module = importlib.import_module("fitz")
    with module.open(path) as document:
        return "\n".join(page.get_text() or "" for page in document)


EXTRACTORS: tuple[tuple[str, str, Callable[[Path], str]], ...] = (
    ("pypdf", "pypdf", _pypdf_text),
    ("pdfplumber", "pdfplumber", _pdfplumber_text),
    ("pymupdf", "fitz", _pymupdf_text),
)


def compare(path: Path) -> dict[str, object]:
    """Run every available extractor and retain independent results."""
    results: dict[str, object] = {"input": str(path), "libraries": {}}
    libraries = results["libraries"]
    assert isinstance(libraries, dict)
    for label, import_name, extractor in EXTRACTORS:
        started = time.perf_counter()
        try:
            importlib.import_module(import_name)
            text = extractor(path)
        except ImportError as exc:
            libraries[label] = {
                "status": "missing",
                "elapsed_seconds": round(time.perf_counter() - started, 6),
                "text_length": 0,
                "error": str(exc),
            }
        except Exception as exc:  # keep one backend failure from stopping the comparison
            libraries[label] = {
                "status": "error",
                "elapsed_seconds": round(time.perf_counter() - started, 6),
                "text_length": 0,
                "error": str(exc),
            }
        else:
            libraries[label] = {
                "status": "ok",
                "elapsed_seconds": round(time.perf_counter() - started, 6),
                "text_length": len(text),
                "error": None,
            }
    return results


def write_results(path: Path, results: dict[str, object]) -> None:
    """Write stable, human-readable JSON results."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    """Run the comparison without requiring every optional dependency."""
    parser = argparse.ArgumentParser(description="Compare PDF text extraction libraries")
    parser.add_argument("pdf", nargs="?", type=Path, default=DEFAULT_PDF)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    if not args.pdf.is_file():
        print(f"PDF file does not exist: {args.pdf}", file=sys.stderr)
        return 1
    try:
        write_results(args.output, compare(args.pdf))
    except OSError as exc:
        print(f"cannot write comparison results: {exc}", file=sys.stderr)
        return 1
    print(f"Comparison results: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
