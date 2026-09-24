"""Network-free tests for the optional PDF exploration commands."""

from __future__ import annotations

import json
import sys
import types
from pathlib import Path

from ebolalens.exploration import compare_libs, pdf_inspect


class FakePage:
    def extract_text(self) -> str:
        return "Synthetic EbolaLens PDF"


class FakeReader:
    def __init__(self, path: Path) -> None:
        assert path.read_bytes().startswith(b"%PDF-")
        self.pages = [FakePage()]
        self.metadata = {"/Author": "EbolaLens tests", "/Title": "Synthetic report"}


def test_pdf_inspect_writes_first_page_text(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.setitem(sys.modules, "pypdf", types.SimpleNamespace(PdfReader=FakeReader))
    output = tmp_path / "inspect.txt"

    result = pdf_inspect.main([str(pdf_inspect.DEFAULT_PDF), "--output", str(output)])

    assert result == 0
    assert output.read_text(encoding="utf-8") == "Synthetic EbolaLens PDF"
    stdout = capsys.readouterr().out
    assert "Pages: 1" in stdout
    assert "Author: EbolaLens tests" in stdout


def test_pdf_inspect_handles_missing_file(tmp_path: Path, capsys) -> None:
    result = pdf_inspect.main([str(tmp_path / "missing.pdf")])

    assert result == 1
    assert "does not exist" in capsys.readouterr().err


def test_compare_libs_records_results_when_dependencies_are_missing(
    tmp_path: Path, monkeypatch
) -> None:
    real_import = compare_libs.importlib.import_module

    def controlled_import(name: str):
        if name == "pypdf":
            return types.SimpleNamespace(PdfReader=FakeReader)
        raise ImportError(f"optional test dependency missing: {name}")

    monkeypatch.setattr(compare_libs.importlib, "import_module", controlled_import)
    output = tmp_path / "comparison.json"
    result = compare_libs.main(
        [str(compare_libs.DEFAULT_PDF), "--output", str(output)]
    )
    monkeypatch.setattr(compare_libs.importlib, "import_module", real_import)

    assert result == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["libraries"]["pypdf"]["status"] == "ok"
    assert payload["libraries"]["pypdf"]["text_length"] > 0
    assert payload["libraries"]["pdfplumber"]["status"] == "missing"
    assert payload["libraries"]["pymupdf"]["status"] == "missing"
