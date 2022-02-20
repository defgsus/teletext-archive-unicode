import io
import json
from typing import List, Optional, TextIO, Tuple, Union

from ..console import ConsoleColors
from .unico import (
    G0_TO_UNICODE_MAPPING, G1_TO_UNICODE_MAPPING, G3_TO_UNICODE_MAPPING
)


class TeletextPage:
    """
    Single page representation.

    Colors:
        https://en.wikipedia.org/wiki/Videotex_character_set#C1_control_codes

    G1 and G3 to unicode mapping:
        https://en.wikipedia.org/wiki/Teletext_character_set#Graphics_character_sets
    """
    
    COLOR_CONSOLE_MAPPING = {
        "b": ConsoleColors.BLACK,
        "r": ConsoleColors.RED,
        "g": ConsoleColors.GREEN,
        "y": ConsoleColors.YELLOW,
        "l": ConsoleColors.BLUE,
        "m": ConsoleColors.PURPLE,
        "c": ConsoleColors.CYAN,
        "w": ConsoleColors.WHITE,
    }

    BOOL_RGB_TO_TELETEXT_MAPPING = {
        (False, False, False): "b",
        (True, False, False): "r",
        (False, True, False): "g",
        (True, True, False): "y",
        (False, False, True): "l",
        (True, False, True): "m",
        (False, True, True): "c",
        (True, True, True): "w",
    }

    class Block:
        def __init__(
                self,
                text: str,
                color: Optional[str] = None,
                bg_color: Optional[str] = None,
                char_set: int = 0,
                link: Optional[Union[int, Tuple[int, int], List[int]]] = None,
        ):
            assert color is None or color in TeletextPage.COLOR_CONSOLE_MAPPING, color
            assert bg_color is None or bg_color in TeletextPage.COLOR_CONSOLE_MAPPING, bg_color
            self.text = text
            self.color = color
            self.bg_color = bg_color
            self.char_set = char_set
            self._link = None
            self.link = link

        def __eq__(self, other) -> bool:
            if not isinstance(other, self.__class__):
                return False
            return self.text == other.text and not self.has_different_attribute(other)

        @property
        def link(self) -> Union[int, List[int]]:
            return self._link

        @link.setter
        def link(self, link: Optional[Union[int, Tuple[int, int], List[int]]]):
            if isinstance(link, (tuple, list)):
                self._link = [int(l) for l in link]
                if len(self._link) == 1:
                    self._link = self._link[0]
                elif len(self._link) != 2:
                    raise ValueError(f"Invalid block link {link}")
            else:
                self._link = int(link) if link is not None else None

        def has_different_attribute(self, other: "Block") -> bool:
            return self.color != other.color \
                or self.bg_color != other.bg_color \
                or self.char_set != other.char_set \
                or self.link != other.link

        def splitlines(self) -> List["Block"]:
            if "\n" not in self.text:
                return [self]
            return [
                self.__class__(line, self.color, self.bg_color, self.char_set)
                for line in self.text.splitlines()
            ]

        def to_json(self) -> list:
            color = "".join((self.color or "_", self.bg_color or "_"))
            if self.char_set:
                color += str(self.char_set)
            attrs = [color]

            if self.link:
                if isinstance(self.link, (list, tuple)):
                    attrs.append(list(self.link))
                else:
                    attrs.append(self.link)

            return attrs + [self.text]

        def to_ansi(self, colors: bool = True) -> str:
            block_str = self.text

            if colors:
                block_str = ConsoleColors.escape(
                    TeletextPage.COLOR_CONSOLE_MAPPING[self.color or "w"],
                    TeletextPage.COLOR_CONSOLE_MAPPING[self.bg_color or "b"]
                ) + block_str + ConsoleColors.escape()

            return block_str

        @classmethod
        def from_json(cls, block: List) -> "Block":
            kwargs = {
                "text": block[-1],
                "color": block[0][0] if block[0][0] != "_" else None,
                "bg_color": block[0][1] if block[0][1] != "_" else None,

            }
            if len(block[0]) > 2:
                kwargs["char_set"] = int(block[0][2])

            return cls(**kwargs)

    def __init__(self):
        self.lines = []
        self.index = 100
        self.sub_index = 1
        self.timestamp = None
        self.error = None

    def __eq__(self, other) -> bool:
        """Only compares the content!"""
        if not isinstance(other, TeletextPage):
            return False
        return self.lines == other.lines

    def new_line(self):
        self.lines.append([])
        if len(self.lines) > 1:
            self.lines[-2] = self._simplify_line(self.lines[-2])

    def add_block(self, block: Block):
        if "\n" not in block.text:
            self.lines[-1].append(block)
        else:
            line_blocks = block.splitlines()
            for i, b in enumerate(line_blocks):
                self.lines[-1].append(b)
                if i + 1 < len(line_blocks):
                    self.new_line()

    def to_ndjson(self, file: Optional[TextIO] = None) -> Optional[str]:
        if file is None:
            file = io.StringIO()
            self.to_ndjson(file)
            file.seek(0)
            return file.read()

        header = {
            "page": self.index,
            "sub_page": self.sub_index,
            "timestamp": self.timestamp,
        }
        if self.error:
            header["error"] = self.error
        print(json.dumps(header, ensure_ascii=False, separators=(',', ':')), file=file)
        if not self.error:
            for line in self.lines:
                json_line = [b.to_json() for b in line]
                print(json.dumps(json_line, ensure_ascii=False, separators=(',', ':')), file=file)

    def to_ansi(self, file: Optional[TextIO] = None, colors: bool = True) -> Optional[str]:
        if file is None:
            file = io.StringIO()
            self.to_ansi(file, colors=colors)
            file.seek(0)
            return file.read()

        for line in self.lines:

            for block in line:
                block_str = block.to_ansi(colors=colors)
                print(block_str, end="", file=file)

            print(file=file)

    @classmethod
    def from_matrix(cls, matrix: List[List[Tuple[str, str]]]) -> "TeletextPage":
        tt = cls()
        for row in matrix:
            tt.new_line()
            prev_color = None
            block = cls.Block("")
            for char, color in row:
                if color != prev_color:
                    if block.text:
                        tt.add_block(block)
                        block = cls.Block("")
                    block.color, block.bg_color = color
                    prev_color = color
                block.text += char

            if block.text:
                tt.add_block(block)

        return tt

    @classmethod
    def g0_to_unicode(cls, code: int) -> int:
        #if code not in cls.G1_TO_UNICODE_MAPPING:
        #    print(f"unrecognized {code:x}")
        return G0_TO_UNICODE_MAPPING.get(code, ord("?"))

    @classmethod
    def g1_to_unicode(cls, code: int) -> int:
        #if code not in cls.G1_TO_UNICODE_MAPPING:
        #    print(f"unrecognized {code:x}")
        return G1_TO_UNICODE_MAPPING.get(code, ord("?"))

    @classmethod
    def g3_to_unicode(cls, code: int) -> int:
        return G3_TO_UNICODE_MAPPING.get(code, ord("?"))

    @classmethod
    def rgb_to_teletext(cls, x: Union[str]) -> str:
        if isinstance(x, str):
            if len(x) == 3:
                rgb = int(x, 16)
                rgb = (
                    ((rgb >> 8) & 0xf) > 5,
                    ((rgb >> 4) & 0xf) > 5,
                    (rgb & 0xf) > 5,
                )
            elif len(x) == 6:
                rgb = int(x, 16)
                rgb = (
                    ((rgb >> 16) & 0xff) > 0x50,
                    ((rgb >> 8) & 0xff) > 0x50,
                    (rgb & 0xff) > 0x50,
                )
            else:
                raise ValueError(f"Can't convert rgb value '{x}'")

            return cls.BOOL_RGB_TO_TELETEXT_MAPPING[rgb]
        else:
            raise TypeError(f"Can't convert rgb value '{x}' of type {type(x).__name__}")

    def _simplify_line(self, line: List[Block]) -> List[Block]:
        """
        Merge blocks of equal attributes together

        Returns new list but blocks may have changed!
        """
        simple_line = []
        prev_block = None
        for block in line:
            if not prev_block:
                prev_block = block
            elif block.has_different_attribute(prev_block):
                simple_line.append(prev_block)
                prev_block = block
            else:
                prev_block.text += block.text

        if prev_block:
            simple_line.append(prev_block)

        return simple_line

