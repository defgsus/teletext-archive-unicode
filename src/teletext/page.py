import io
import json
from typing import List, Optional, TextIO, Tuple, Union

from ..console import ConsoleColors as CC
from ..words import tokenize, concat_split_words
from .unico import (
    G0_TO_UNICODE_MAPPING, G1_TO_UNICODE_MAPPING, G3_TO_UNICODE_MAPPING,
    RE_ANSI_ESCAPE
)


class TeletextPage:
    """
    Single page representation.

    This class wraps between the encoded ndjson file format
    and the ANSI representation. It also helps to scrape the pages.

    Colors:
        https://en.wikipedia.org/wiki/Videotex_character_set#C1_control_codes

    G1 and G3 to unicode mapping:
        https://en.wikipedia.org/wiki/Teletext_character_set#Graphics_character_sets
    """
    
    COLOR_CONSOLE_MAPPING = {
        "b": CC.BLACK,
        "r": CC.RED,
        "g": CC.GREEN,
        "y": CC.YELLOW,
        "l": CC.BLUE,
        "m": CC.PURPLE,
        "c": CC.CYAN,
        "w": CC.WHITE,
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
        """
        Representation of a text block with it's attributes like
         - foreground and background color
         - the extended character set
         - a teletext page link
        """
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
                block_str = CC.escape(
                    TeletextPage.COLOR_CONSOLE_MAPPING[self.color or "w"],
                    TeletextPage.COLOR_CONSOLE_MAPPING[self.bg_color or "b"]
                ) + block_str + CC.escape()

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

            if len(block) > 2:
                kwargs["link"] = block[1]

            return cls(**kwargs)

    def __init__(self):
        self.lines = []
        self.index = 100
        self.sub_index = 1
        self.timestamp: str = None
        self.error: str = None
        self.category: str = None

    def __str__(self):
        return f"{self.index}/{self.sub_index}({len(self.lines)} lines)"

    def __eq__(self, other) -> bool:
        """
        Only compares the content, not the timestamp or index!
        """
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

    def to_ansi(self, file: Optional[TextIO] = None, colors: bool = True, border: bool = False) -> Optional[str]:
        if file is None:
            file = io.StringIO()
            self.to_ansi(file, colors=colors, border=border)
            file.seek(0)
            return file.read()

        if not border:
            for line in self.lines:
                for block in line:
                    block_str = block.to_ansi(colors=colors)
                    print(block_str, end="", file=file)

                print(file=file)

        else:
            lines = [
                "".join(block.to_ansi(colors=False) for block in line)
                for line in self.lines
            ]
            width = max(0, 0, *(len(l) for l in lines))

            if colors:
                color_lines = [
                    "".join(block.to_ansi(colors=True) for block in line)
                    for line in self.lines
                ]

                c = CC.escape(CC.WHITE, bright=False)
                off = CC.escape()
                print(c + "▛" + "▀" * width + "▜" + off, file=file)
                for c_line, line in zip(color_lines, lines):
                    print(c + "▌" + off + c_line + " " * (width - len(line)) + c + "▐" + off, file=file)
                print(c + "▙" + "▄" * width + "▟" + off, file=file)
            else:
                print("▛" + "▀" * width + "▜", file=file)
                for line in lines:
                    print("▌" + line + " " * (width - len(line)) + "▐", file=file)
                print("▙" + "▄" * width + "▟", file=file)

    def to_html(self, css: bool = False, file: Optional[TextIO] = None) -> Optional[str]:
        from .html_renderer import TeletextHtmlRenderer
        if file is None:
            file = io.StringIO()
            self.to_html(css=css, file=file)
            file.seek(0)
            return file.read()

        renderer = TeletextHtmlRenderer()
        if css:
            print("""<style>""", file=file)
            renderer.css(file=file)
            print("""</style>""", file=file)
        renderer.render(self, file=file)

    def to_image(self):
        from .image_renderer import TeletextImageRenderer
        renderer = TeletextImageRenderer()
        return renderer.render(self)

    def to_text(self, concat_split_words: bool = True) -> str:
        """
        Returns everything that is not graphics or numbers.

        Also concats bro-
        ken lines together.
        """
        texts = []
        for line in self.lines:
            for block in line:
                for c in block.text:
                    if ord(c) < 0x1bf00 and not 0x2500 <= ord(c) < 0x2600 and not "0" <= c <= "9":
                        texts.append(c)

            texts.append("\n")
        text = "".join(texts)

        if concat_split_words:
            text = globals()["concat_split_words"](text)
        return text

    def to_tokens(self, lowercase: bool = False, concat_split_words: bool = True) -> List[str]:
        text = self.to_text(concat_split_words=concat_split_words)
        return tokenize(text, lowercase=lowercase)

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

        Returns new list but the Block instances may have changed!
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

