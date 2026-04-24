from __future__ import annotations

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
        raise RenderDependencyError("PDF rendering requires optional dependency `reportlab`. Install with `python3 -m pip install '.[render]'`.") from exc

    path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(path), pagesize=A4)
    width, height = A4
    x = 48
    y = height - 48
    for line in text.splitlines():
        if y < 48:
            pdf.showPage()
            y = height - 48
        safe = line.encode("latin-1", "replace").decode("latin-1")
        pdf.drawString(x, y, safe[:120])
        y -= 14
    pdf.save()


def _render_docx(path: Path, text: str) -> None:
    try:
        from docx import Document
    except ImportError as exc:
        raise RenderDependencyError("DOCX rendering requires optional dependency `python-docx`. Install with `python3 -m pip install '.[render]'`.") from exc

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
