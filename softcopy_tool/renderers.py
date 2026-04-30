from __future__ import annotations

import os
from pathlib import Path


SUPPORTED_FORMATS = {"md", "pdf", "docx"}


class RenderDependencyError(RuntimeError):
    pass


def normalize_formats(raw: str | list[str] | tuple[str, ...] | None) -> list[str]:
    if raw is None:
        values = ["md"]
    elif isinstance(raw, str):
        values = [item.strip().lower() for item in raw.split(",") if item.strip()]
    else:
        values = [str(item).strip().lower() for item in raw if str(item).strip()]
    unknown = sorted(set(values) - SUPPORTED_FORMATS)
    if unknown:
        raise ValueError(f"Unsupported output format(s): {', '.join(unknown)}")
    return values or ["md"]


def render_optional_outputs(markdown_path: Path, formats: list[str]) -> list[str]:
    written: list[str] = []
    text = markdown_path.read_text(encoding="utf-8")
    if "pdf" in formats:
        _render_pdf(markdown_path.with_suffix(".pdf"), text)
        written.append(str(markdown_path.with_suffix(".pdf")))
    if "docx" in formats:
        _render_docx(markdown_path.with_suffix(".docx"), text)
        written.append(str(markdown_path.with_suffix(".docx")))
    return written


def _render_pdf(path: Path, text: str) -> None:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
    except ImportError as exc:
        raise RenderDependencyError(
            "PDF rendering requires optional dependency `reportlab`. "
            "Install with `python3 -m pip install '.[render]'`."
        ) from exc

    path.parent.mkdir(parents=True, exist_ok=True)
    font_name = _register_pdf_font()
    pdf = canvas.Canvas(str(path), pagesize=A4)
    _, height = A4
    x = 48
    y = height - 48
    pdf.setFont(font_name, 10)
    for line in text.splitlines():
        if y < 48:
            pdf.showPage()
            pdf.setFont(font_name, 10)
            y = height - 48
        pdf.drawString(x, y, line[:120])
        y -= 14
    pdf.save()


def _register_pdf_font() -> str:
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.cidfonts import UnicodeCIDFont
        from reportlab.pdfbase.ttfonts import TTFont
    except ImportError as exc:
        raise RenderDependencyError(
            "PDF rendering requires optional dependency `reportlab`. "
            "Install with `python3 -m pip install '.[render]'`."
        ) from exc

    configured = os.environ.get("SOFTCOPY_CJK_FONT")
    if configured:
        font_path = Path(configured).expanduser()
        if not font_path.exists():
            raise RenderDependencyError(f"Configured CJK font does not exist: {font_path}")
        try:
            pdfmetrics.registerFont(TTFont("SoftCopyCJK", str(font_path)))
            return "SoftCopyCJK"
        except Exception as exc:
            raise RenderDependencyError(f"Could not load configured CJK font: {font_path}") from exc

    try:
        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
        return "STSong-Light"
    except Exception:
        pass

    for font_path in _candidate_cjk_font_paths():
        if not font_path.exists():
            continue
        try:
            pdfmetrics.registerFont(TTFont("SoftCopyCJK", str(font_path)))
            return "SoftCopyCJK"
        except Exception:
            continue

    raise RenderDependencyError(
        "PDF rendering needs a CJK-capable font. Set SOFTCOPY_CJK_FONT=/path/to/font.ttf."
    )


def _candidate_cjk_font_paths() -> list[Path]:
    return [
        Path("/Library/Fonts/Arial Unicode.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
        Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttf"),
        Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttf"),
    ]


def _render_docx(path: Path, text: str) -> None:
    try:
        from docx import Document
    except ImportError as exc:
        raise RenderDependencyError(
            "DOCX rendering requires optional dependency `python-docx`. "
            "Install with `python3 -m pip install '.[render]'`."
        ) from exc

    path.parent.mkdir(parents=True, exist_ok=True)
    document = Document()
    for line in text.splitlines():
        if line.startswith("# "):
            document.add_heading(line[2:].strip(), level=1)
        elif line.startswith("## "):
            document.add_heading(line[3:].strip(), level=2)
        elif line.startswith("### "):
            document.add_heading(line[4:].strip(), level=3)
        else:
            document.add_paragraph(line)
    document.save(path)
