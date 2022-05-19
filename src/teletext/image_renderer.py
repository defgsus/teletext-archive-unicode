import io
from typing import Optional, List

from PIL import Image, ImageFont, ImageDraw

from .page import TeletextPage


class TeletextImageRenderer:

    COLORS = {
        "b": (0, 0, 0),
        "r": (255, 0, 0),
        "g": (0, 255, 0),
        "y": (255, 255, 0),
        "l": (0, 0, 255),
        "m": (255, 0, 255),
        "c": (0, 255, 255),
        "w": (255, 255, 255),
    }

    def __init__(self, width: int = 40, height: int = 25, cell_width: int = 8, cell_height: int = 8):
        self.width = width
        self.height = height
        self.cell_width = cell_width
        self.cell_height = cell_height
        self._font = None

    @property
    def font(self):
        if self._font is None:
            self._font = ImageFont.truetype("/home/bergi/.local/share/fonts/unscii-8.ttf", 8)
        return self._font

    def render(self, page: TeletextPage) -> Image.Image:
        image = Image.new("RGB", (self.width * self.cell_width, self.height * self.cell_height))
        draw = ImageDraw.ImageDraw(image)

        y = 0
        for line in page.lines:
            if y >= (self.height - 1) * self.cell_height:
                continue
            x = 0
            for block in line:
                for c in block.text:
                    if x < (self.width + 1) * self.cell_width:
                        draw.rectangle(
                            ((x, y), (x + self.cell_width, y + self.cell_height)),
                            fill=self.COLORS.get(block.bg_color, (0, 0, 0))
                        )
                        draw.text(
                            (x, y), c,
                            font=self.font,
                            fill=self.COLORS.get(block.color, (255, 255, 255)),
                        )
                    x += self.cell_width

            y += self.cell_height
        return image
