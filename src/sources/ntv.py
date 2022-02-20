import json
from typing import Dict, Generator, Tuple, Union, Optional

from ..scraper import Scraper
from ..teletext import Teletext, TeletextPage


class NTV(Scraper):

    NAME = "ntv"
    FILE_EXTENSION = "json"

    def iter_pages(self) -> Generator[Tuple[int, int, dict], None, None]:
        url = f"https://teletext.n-tv.de/teletext-api/100/0"

        page_index = 0
        while page_index < 900:
            data = self.get_html(url).json()

            new_page_index = int(data["content"]["page"][:3])
            if new_page_index <= page_index:
                break
            page_index = new_page_index

            yield page_index, 1, data

            for sub_page_index in data["subpages"]["subpage"][1:]:
                sub_page_index = int(sub_page_index)
                url = f"https://teletext.n-tv.de/teletext-api/{page_index}/{sub_page_index}"
                sub_data = self.get_html(url).json()

                yield page_index, sub_page_index, sub_data

            # get next page
            url = f"https://teletext.n-tv.de/teletext-api/ascend/{page_index}"

    def compare_pages(self, old: TeletextPage, new: TeletextPage) -> bool:
        if len(old.lines) != len(new.lines):
            return False
        if len(old.lines) < 1:
            return False
        # compare pages without the first line which includes the current date and time
        return old.lines[1:] == new.lines[1:]

    def to_teletext(self, content: dict) -> TeletextPage:
        matrix = []
        for row in content["content"]["row"]:
            matrix_row = []
            for col in row["columns"]:
                if col.get("graphic"):
                    char = chr(TeletextPage.g1_to_unicode(int(col["value"])))
                else:
                    char = col["value"]

                color = "".join((
                    TeletextPage.rgb_to_teletext(col["font"][1:]),
                    TeletextPage.rgb_to_teletext(col["background"][1:]),
                ))
                matrix_row.append((char, color))
            matrix.append(matrix_row)

        return TeletextPage.from_matrix(matrix)
