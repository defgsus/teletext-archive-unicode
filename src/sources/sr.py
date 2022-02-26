import json
from typing import Dict, Generator, Tuple, Union, Optional, Any

import bs4

from ..scraper import Scraper
from ..teletext import Teletext, TeletextPage


class SR(Scraper):

    NAME = "sr"

    PAGE_CATEGORIES = {
        100: "index",
        110: "news",
        160: "weather",
        200: "sport",
        300: "program",
        470: "undefined",
        500: "service",
        520: "lotto",
        540: "traffic",
        560: "culture",
        598: "traffic",
        600: "sport",
        700: "undefined",
        810: "extra",
    }

    def iter_pages(self) -> Generator[Tuple[int, int, bs4.BeautifulSoup], None, None]:

        page_index = 100
        sub_page_index = 1
        while page_index < 900:
            url = f"https://www.saartext.de/{page_index}/{sub_page_index:02d}"
            soup = self.get_soup(url)

            yield page_index, sub_page_index, soup

            next_a = soup.find("a", {"id": "nextButton"})
            next_page = next_a["href"].strip("/").split("/")

            new_page_index = int(next_page[0])
            if len(next_page) == 1:
                sub_page_index = 1
            else:
                sub_page_index = int(next_page[1].lstrip("0"))

            if new_page_index < page_index:
                break

            page_index = new_page_index

    def compare_pages(self, old: TeletextPage, new: TeletextPage) -> bool:
        if len(old.lines) != len(new.lines):
            return False
        if len(old.lines) < 1:
            return False
        # compare pages without the first line which includes the current date and time
        return old.lines[1:] == new.lines[1:]

    def to_teletext(self, content: bs4.BeautifulSoup) -> TeletextPage:
        tt = TeletextPage()
        tt.new_line()
        for elem in content.find("pre", {"class": "saartext_page"}).children:

            if isinstance(elem, bs4.NavigableString):
                tt.add_block(TeletextPage.Block(elem))

            elif elem.name == "a":
                link = tuple(int(n) for n in filter(bool, elem["href"].split("/")))
                tt.add_block(TeletextPage.Block(elem.text, link=link))

            else:
                self.log(f"unhandled element {elem}")

        return tt

    @classmethod
    def legacy_bytes_to_content(cls, content: bytes) -> Any:
        return cls.to_soup(content.decode("utf-8"))
