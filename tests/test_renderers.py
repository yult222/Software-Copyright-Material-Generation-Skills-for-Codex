from __future__ import annotations

import importlib.util
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from softcopy_tool import renderers


class FakeCanvas:
    instances: list["FakeCanvas"] = []

    def __init__(self, path: str, pagesize: tuple[int, int]) -> None:
        self.path = path
        self.pagesize = pagesize
        self.drawn: list[str] = []
        FakeCanvas.instances.append(self)

    def setFont(self, font_name: str, font_size: int) -> None:
        self.font_name = font_name
        self.font_size = font_size

    def drawString(self, x: int, y: int, text: str) -> None:
        self.drawn.append(text)

    def stringWidth(self, text: str, font_name: str, font_size: int) -> float:
        return len(text) * font_size * 0.5

    def showPage(self) -> None:
        pass

    def save(self) -> None:
        Path(self.path).write_bytes(b"%PDF-fake\n")


class RendererPdfTests(unittest.TestCase):
    def test_pdf_renderer_passes_chinese_text_without_latin1_replacement(self) -> None:
        fake_reportlab = {
            "reportlab": types.ModuleType("reportlab"),
            "reportlab.lib": types.ModuleType("reportlab.lib"),
            "reportlab.lib.pagesizes": types.ModuleType("reportlab.lib.pagesizes"),
            "reportlab.pdfgen": types.ModuleType("reportlab.pdfgen"),
            "reportlab.pdfgen.canvas": types.ModuleType("reportlab.pdfgen.canvas"),
        }
        fake_reportlab["reportlab.lib.pagesizes"].A4 = (595, 842)
        fake_reportlab["reportlab.pdfgen.canvas"].Canvas = FakeCanvas
        fake_reportlab["reportlab.pdfgen"].canvas = fake_reportlab["reportlab.pdfgen.canvas"]
        FakeCanvas.instances = []

        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "manual.pdf"
            with patch.dict("sys.modules", fake_reportlab):
                with patch.object(renderers, "_register_pdf_font", return_value="FakeCJK"):
                    renderers._render_pdf(output, "软件著作权登记")

        self.assertEqual(FakeCanvas.instances[-1].drawn, ["软件著作权登记"])

    def test_pdf_renderer_wraps_without_dropping_long_lines(self) -> None:
        fake_reportlab = {
            "reportlab": types.ModuleType("reportlab"),
            "reportlab.lib": types.ModuleType("reportlab.lib"),
            "reportlab.lib.pagesizes": types.ModuleType("reportlab.lib.pagesizes"),
            "reportlab.pdfgen": types.ModuleType("reportlab.pdfgen"),
            "reportlab.pdfgen.canvas": types.ModuleType("reportlab.pdfgen.canvas"),
        }
        fake_reportlab["reportlab.lib.pagesizes"].A4 = (595, 842)
        fake_reportlab["reportlab.pdfgen.canvas"].Canvas = FakeCanvas
        fake_reportlab["reportlab.pdfgen"].canvas = fake_reportlab["reportlab.pdfgen.canvas"]
        FakeCanvas.instances = []
        long_line = "A" * 180

        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "manual.pdf"
            with patch.dict("sys.modules", fake_reportlab):
                with patch.object(renderers, "_register_pdf_font", return_value="FakeCJK"):
                    renderers._render_pdf(output, long_line)

        self.assertEqual("".join(FakeCanvas.instances[-1].drawn), long_line)
        self.assertGreater(len(FakeCanvas.instances[-1].drawn), 1)

    def test_font_registration_error_lists_failed_fallbacks(self) -> None:
        fake_reportlab = {
            "reportlab": types.ModuleType("reportlab"),
            "reportlab.pdfbase": types.ModuleType("reportlab.pdfbase"),
            "reportlab.pdfbase.pdfmetrics": types.ModuleType("reportlab.pdfbase.pdfmetrics"),
            "reportlab.pdfbase.cidfonts": types.ModuleType("reportlab.pdfbase.cidfonts"),
            "reportlab.pdfbase.ttfonts": types.ModuleType("reportlab.pdfbase.ttfonts"),
        }

        class FakeCIDFont:
            def __init__(self, name: str) -> None:
                self.name = name

        class FakeTTFont:
            def __init__(self, name: str, path: str) -> None:
                self.name = name
                self.path = path

        def reject_font(font: object) -> None:
            raise RuntimeError("cannot load font")

        fake_reportlab["reportlab.pdfbase.pdfmetrics"].registerFont = reject_font
        fake_reportlab["reportlab.pdfbase.cidfonts"].UnicodeCIDFont = FakeCIDFont
        fake_reportlab["reportlab.pdfbase.ttfonts"].TTFont = FakeTTFont

        with tempfile.TemporaryDirectory() as temp_dir:
            font_path = Path(temp_dir) / "Fake.ttf"
            font_path.write_text("not a font", encoding="utf-8")
            with patch.dict("sys.modules", fake_reportlab):
                with patch.object(renderers, "_candidate_cjk_font_paths", return_value=[font_path]):
                    with self.assertRaises(renderers.RenderDependencyError) as raised:
                        renderers._register_pdf_font()

        message = str(raised.exception)
        self.assertIn("STSong-Light", message)
        self.assertIn(str(font_path), message)


class RendererDocxTests(unittest.TestCase):
    def test_docx_header_text_uses_chinese_material_metadata(self) -> None:
        text = "\n".join(
            [
                "# 源程序鉴别材料",
                "",
                "- 软件名称：示例系统",
                "- 版本号：V1.0",
                "- 材料类型：源程序鉴别材料",
            ]
        )

        self.assertEqual(renderers._docx_header_text(text), "示例系统 V1.0 源程序鉴别材料")

    @unittest.skipIf(importlib.util.find_spec("docx") is None, "python-docx is not installed")
    def test_docx_renderer_preserves_chinese_text_and_code_blocks(self) -> None:
        from docx import Document

        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "code_doc.docx"
            renderers._render_docx(
                output,
                "\n".join(
                    [
                        "# 源程序鉴别材料",
                        "",
                        "- 软件名称：示例系统",
                        "- 版本号：V1.0",
                        "",
                        "## 分页源程序",
                        "- 中文列表项",
                        "```text",
                        "    def main():",
                        "        return 'ok'",
                        "```",
                    ]
                ),
            )

            paragraphs = [item.text for item in Document(output).paragraphs]

        self.assertIn("源程序鉴别材料", paragraphs)
        self.assertIn("中文列表项", paragraphs)
        self.assertIn("    def main():", paragraphs)
        self.assertIn("        return 'ok'", paragraphs)


if __name__ == "__main__":
    unittest.main()
