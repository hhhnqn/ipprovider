"""CLI: flag --ocr reenviado a extract_text."""

from pathlib import Path

import pytest

from ipprovider.cli import main


def test_main_passes_ocr_flags_to_extract(tmp_path, monkeypatch):
    pytest.importorskip("docx")
    from docx import Document

    doc_path = tmp_path / "x.docx"
    Document().save(doc_path)
    out = tmp_path / "out.html"

    captured: dict[str, object] = {}

    def fake_extract(
        path: Path,
        *,
        progress: bool = False,
        ocr: bool = False,
        ocr_lang: str | None = None,
    ) -> str:
        captured["path"] = path
        captured["progress"] = progress
        captured["ocr"] = ocr
        captured["ocr_lang"] = ocr_lang
        return "192.168.50.1"

    monkeypatch.setattr("ipprovider.cli.extract_text", fake_extract)

    rc = main([str(doc_path), "-o", str(out), "--ocr", "--ocr-lang", "eng", "-q"])
    assert rc == 0
    assert captured["ocr"] is True
    assert captured["ocr_lang"] == "eng"
    assert out.is_file()


def test_main_ocr_without_lang(tmp_path, monkeypatch):
    pytest.importorskip("docx")
    from docx import Document

    doc_path = tmp_path / "y.docx"
    Document().save(doc_path)
    out = tmp_path / "out2.html"

    captured: dict[str, object] = {}

    def fake_extract(
        path: Path,
        *,
        progress: bool = False,
        ocr: bool = False,
        ocr_lang: str | None = None,
    ) -> str:
        captured["ocr"] = ocr
        captured["ocr_lang"] = ocr_lang
        return "192.168.50.2"

    monkeypatch.setattr("ipprovider.cli.extract_text", fake_extract)

    rc = main([str(doc_path), "-o", str(out), "--ocr", "-q"])
    assert rc == 0
    assert captured["ocr"] is True
    assert captured["ocr_lang"] is None
