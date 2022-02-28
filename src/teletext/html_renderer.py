import io
from typing import Optional, TextIO, List

from .page import TeletextPage


class TeletextHtmlRenderer:

    COLORS = {
        "b": "000000",
        "r": "ff0000",
        "g": "00ff00",
        "y": "ffff00",
        "l": "0000ff",
        "m": "ff00ff",
        "c": "00ffff",
        "w": "ffffff",
    }

    def __init__(self, width: int = 40, height: int = 25, cell_width: int = 8, cell_height: int = 16):
        self.width = width
        self.height = height
        self.cell_width = cell_width
        self.cell_height = cell_height

    def css(self, file: Optional[TextIO] = None) -> Optional[str]:
        if file is None:
            file = io.StringIO()
            self.css(file=file)
            file.seek(0)
            return file.read()

        print(f"""
        .vt {{
            width: {self.width * self.cell_width}px;
            height: {self.height * self.cell_height}px;
            line-height: normal;
        }}
        .vt .vt-line {{
            height: {self.cell_height}px;
        }}
        .vt .vt-block {{
            display: inline-block;
        }}
        .vt .vt-char {{
            display: inline-block;
            width: {self.cell_width}px;
            height: {self.cell_height}px;
            font-size: {self.cell_height}px;
            font-family: unscii, mono;
        }}
        """, file=file)
        for code, color in self.COLORS.items():
            print(f""".vt .vt-f{code} {{ color: #{color}; }}""", file=file)
            print(f""".vt .vt-b{code} {{ background-color: #{color}; }}""", file=file)

    def render(self, page: TeletextPage, file: Optional[TextIO] = None) -> Optional[str]:
        if file is None:
            file = io.StringIO()
            self.render(page, file=file)
            file.seek(0)
            return file.read()

        print("""<div class="vt">""", end="", file=file)

        for line in page.lines:
            self._render_line(page, line, file)

        print("""</div>""", file=file)

    def _render_line(self, page: TeletextPage, line: List[TeletextPage.Block], file: TextIO):
        print("""<div class="vt-line">""", end="", file=file)
        for block in line:
            self._render_block(page, block, file)
        print("""</div>""", file=file)

    def _render_block(self, page: TeletextPage, block: TeletextPage.Block, file: TextIO):
        text = block.text.replace("\xa0", " ")
        print(f"""<div class="vt-block vt-f{block.color} vt-b{block.bg_color}">""", end="", file=file)
        print("".join(
            f"""<div class="vt-char">{c}</div>"""
            for c in text
        ), end="", file=file)
        print("""</div>""", end="", file=file)
