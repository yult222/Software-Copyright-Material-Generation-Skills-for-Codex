from __future__ import annotations

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


if __name__ == "__main__":
    unittest.main()
