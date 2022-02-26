import re
import urllib.parse
from typing import Generator, Tuple, Union, Any

import bs4

from ..scraper import Scraper
from ..teletext import Teletext, TeletextPage
from src.teletext.unico import G0_TO_UNICODE_MAPPING

CUSTOM_G0_MAPPING = G0_TO_UNICODE_MAPPING.copy()
CUSTOM_G0_MAPPING.update({
    0xdf: ord("ß"),
    0xd6: ord("Ö"),
    0xf6: ord("ö"),
    0xdc: ord("Ü"),
    0xfc: ord("ü"),
    0xc4: ord("Ä"),
    0xe4: ord("ä"),
    0xb0: ord("°"),
    0xa7: ord("§"),
})


class DreiSAT(Scraper):

    NAME = "3sat"

    _RE_PAGE_URL = re.compile(r".*\?p=(\d\d\d)_(\d\d\d\d)&.*")

    _RE_TTX_STYLES = {
        "top": re.compile(r".*top:\s*(\d+)px"),
        "left": re.compile(r".*left:\s*(\d+)px"),
        "bc": re.compile(r".*background-color:\s*#([0-9a-f]+)"),
        "pos": re.compile(r".*background-position:\s*(-?\d+)px\s+(-?\d+)px"),
    }

    PAGE_CATEGORIES = {
        100: "index",
        111: "news",
        160: "stocks",
        180: "undefined",
        200: "sport",
        280: "lotto",
        300: "program",
        400: "index",
        401: "weather",
        450: "traffic",
        500: "culture",
        600: "index",
        601: "internal",
    }

    def iter_pages(self) -> Generator[Tuple[int, int, Any], None, None]:
        page_index = 100
        sub_page_index = 1

        while page_index < 900:
            url = f"https://blog.3sat.de/ttx/index.php?p={page_index}_{sub_page_index:04d}&c=0"
            soup = self.get_soup(url)

            yield page_index, sub_page_index, soup

            next_page_index, next_sub_page_index = self._get_next_page(soup, "nextsub")

            if next_page_index < page_index:
                break

            if (next_page_index, next_sub_page_index) == (page_index, sub_page_index) \
                    or next_sub_page_index < sub_page_index:
                next_page_index, next_sub_page_index = self._get_next_page(soup, "nextpage")
                if next_page_index < page_index:
                    break

            page_index, sub_page_index = next_page_index, next_sub_page_index

    def _get_next_page(self, soup: bs4.BeautifulSoup, tag_id: str) -> Tuple[int, int]:
        next_a = soup.find("a", {"id": tag_id})
        next_href = urllib.parse.urljoin("https://blog.3sat.de", next_a["href"])

        match = self._RE_PAGE_URL.match(next_href)
        new_page_index, sub_page_index = match.groups()

        return (
            int(new_page_index),
            int(sub_page_index.lstrip("0")),
        )

    def to_teletext(self, content: bs4.BeautifulSoup) -> TeletextPage:

        matrix = [
            [(" ", "wb") for x in range(40)]
            for y in range(26)
        ]
        matrix_codes = [
            [0] * 40
            for y in range(26)
        ]
        for elem in content.find("div", {"id": "ttxbody"}).find_all("div", recursive=False):
            style = elem["style"]
            params = dict()
            for key, regexp in self._RE_TTX_STYLES.items():
                match = regexp.match(style)
                if match:
                    params[key] = match.groups()

            if params.get("pos"):

                cls = elem["class"][0]
                color = "w"
                bg_color = "b"
                is_graphic = False
                if cls.startswith("i-ns-"):
                    color = TeletextPage.rgb_to_teletext(cls[5:8])
                    is_graphic = cls.endswith("g")

                x, y = int(params["left"][0]) // 12, int(params["top"][0]) // 14
                char_x, char_y = int(params["pos"][0]) // 12, int(params["pos"][1]) // 14
                char_code = -char_x - 16 * char_y
                matrix_codes[y][x] = char_code
                #print(f"{char_code:x} ", end="")
                if 0x60 <= char_code <= 0x7f:
                    char = " "
                else:
                    if is_graphic:
                        char = chr(TeletextPage.g1_to_unicode(char_code + 0x20))
                    else:
                        char = chr(CUSTOM_G0_MAPPING.get(char_code + 0x20) or ord("!"))

                matrix[y][x] = (char, color + bg_color)

        #for row in matrix_codes:
        #    print(" ".join(f"{c:2x}" for c in row))

        return TeletextPage.from_matrix(matrix)

    @classmethod
    def legacy_bytes_to_content(cls, content: bytes) -> Any:
        return cls.to_soup(content.decode("utf-8"))
