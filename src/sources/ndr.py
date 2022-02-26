import re
from typing import Dict, Generator, Tuple, Union, Any

import bs4

from ..scraper import Scraper
from ..teletext import Teletext, TeletextPage


class NDR(Scraper):

    NAME = "ndr"

    PAGE_CATEGORIES = {
        100: "index",
        108: "weather",
        112: "news",
        200: "sport",
        300: "program",
        450: "extra",
        500: "index",
        501: "internal",
        520: "health",
        530: "regional",
        540: "cooking",
        550: "program",
        560: "index",
        561: "internal",
        565: "news",
        570: "program",
        590: "cooking",
        600: "index",
        601: "lotto",
        610: "stocks",
        630: "news",
        650: "index",
        651: "weather",
        680: "calendar",
        700: "traffic",
        800: "sport",
        870: "extra",
    }

    COLOR_CLASS_MAPPING = {
        "0": "b",
        "1": "r",
        "2": "g",
        "3": "y",
        "4": "l",
        "5": "m",
        "6": "c",
        "7": "w",
    }

    def iter_pages(self) -> Generator[Tuple[int, int, str], None, None]:
        for page_index, num_sub_pages in self._get_pages().items():
            for sub_page_index in range(num_sub_pages):
                url = f"https://www.ndr.de/public/teletext/{page_index}_{sub_page_index+1:02}.htm"
                response = self.get_html(url)
                if response.status_code == 200:
                    yield page_index, sub_page_index+1, response.text

    def _get_pages(self) -> Dict[int, int]:
        text = self.get_html("https://www.ndr.de/public/teletext/pages.js").text
        pages = dict()
        for match in re.findall(r"(\d+):(\d+)", text):
            pages[int(match[0])] = int(match[1])

        return pages

    def to_teletext(self, content: str) -> TeletextPage:
        soup = self.to_soup(content)
        tt = TeletextPage()
        tt.new_line()
        for elem in soup.find("pre", {"class": "txt"}).children:
            block = TeletextPage.Block("")

            if isinstance(elem, bs4.NavigableString):
                if elem == "\n":
                    tt.new_line()

            elif elem.name == "b":
                classes = elem.get("class")
                if classes:
                    for cls in classes:
                        if cls.startswith("f"):
                            block.color = self.COLOR_CLASS_MAPPING[cls[1:]]
                        elif cls.startswith("b"):
                            block.bg_color = self.COLOR_CLASS_MAPPING[cls[1:]]
                block.text += elem.text
            elif elem.name == "a":
                block.text += elem.text
            else:
                self.log(f"unhandled element {elem}")

            if block.text:
                text = block.text
                block.text = ""
                for c in text:
                    if ord(c) >= 0xe000:
                        g1 = ord(c) - 0xe000

                        if g1 > 0x40:
                            # TODO: set block.char_set (which might require multiple blocks)
                            g1 -= 0x40

                        g1 += 0x20
                        if 0x40 <= g1 <= 0x5f:
                            g1 += 0x20

                        block.text += chr(TeletextPage.g1_to_unicode(g1))
                    else:
                        block.text += c
                tt.add_block(block)

        return tt
