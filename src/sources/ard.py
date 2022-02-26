from typing import Dict, Generator, Tuple, Union, Optional, Any

import bs4

from ..scraper import Scraper
from ..teletext import Teletext, TeletextPage


class ARD(Scraper):

    NAME = "ard"

    COLOR_CLASS_MAPPING = {
        "bl": "l"
    }

    PAGE_CATEGORIES = {
        100: "index",
        101: "news",
        170: "weather",
        200: "sport",
        300: "program",
        400: "culture",
        420: "gossip",
        440: "internal",
        500: "sport",
        570: "extra",
        580: "lotto",
        590: "undefined",
        650: "sport",
        700: "stocks",
        770: "internal",
        790: "index",
        800: "undefined",
    }

    def iter_pages(self) -> Generator[Tuple[int, int, Any], None, None]:
        page_index = 100
        while page_index < 900:
            response = self.get_html(self._get_url(page_index, 1), allow_redirects=False)
            if response.status_code == 302:
                new_page_index = int(response.headers["location"][-3:])
                if new_page_index < page_index:
                    break
                page_index = new_page_index
                continue

            soup = self.to_soup(response.text)
            if soup:
                yield page_index, 1, soup

                sub_page_div = soup.find("div", {"id": "output_unterseite"})
                if sub_page_div:
                    num_pages = int(sub_page_div.text.split("/")[-1])

                    for sub_page_index in range(2, num_pages + 1):
                        sub_soup = self.get_soup(self._get_url(page_index, sub_page_index))
                        if sub_soup:
                            yield page_index, sub_page_index, sub_soup
            page_index += 1

    def _get_url(self, page_index: int, sub_page_index: int) -> str:
        return f"https://www.ard-text.de/index.php?page={page_index}&sub={sub_page_index}"

    def to_teletext(self, soup: bs4.BeautifulSoup) -> Optional[TeletextPage]:
        entry = soup.find("div", {"id": "page_1"})
        if not entry:
            return

        tt = TeletextPage()
        for line in entry.find_all("div"):
            tt.new_line()

            for nobr in line.find_all("nobr"):

                block = TeletextPage.Block("")

                if nobr.parent.name == "span":
                    for cls in nobr.parent.get("class"):
                        if cls.startswith("fg"):
                            block.color = self.COLOR_CLASS_MAPPING.get(cls[2:], cls[2:])
                        elif cls.startswith("bg"):
                            block.bg_color = self.COLOR_CLASS_MAPPING.get(cls[2:], cls[2:])

                for c in nobr.children:
                    if isinstance(c, bs4.NavigableString):
                        block.text += c.text
                    elif c.name == "a":
                        block.text += c.text
                    elif c.name == "img":
                        block.text += self._get_img_tt_char(c.get("src"))
                    else:
                        self.log(f"unhandled element {c}")

                if block.text:
                    tt.add_block(block)

        return tt

    @classmethod
    def _get_img_tt_char(cls, url: str) -> str:
        """
        Convert image url to unicode str

        https://en.wikipedia.org/wiki/Teletext_character_set#G1_block_mosaics
        """
        try:
            code = int(url[-6:-4], 16)
            return chr(TeletextPage.g1_to_unicode(code))
        except ValueError:
            return "?"

    @classmethod
    def legacy_bytes_to_content(cls, content: bytes) -> Any:
        return cls.to_soup(content.decode("utf-8"))
