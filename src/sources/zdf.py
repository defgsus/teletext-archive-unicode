import re
import json
from typing import Dict, Generator, Tuple, Union

from ..scraper import Scraper
from ..teletext import Teletext, TeletextPage


class ZDFBase(Scraper):

    ABSTRACT = True

    ZDF_MANDANT = None

    # minimal encoding fixes
    #   of previous scrapes
    ENCODING_FIX_MAPPING = {
        "Ã": "Ü",
        "Ã¼": "ü",
        "â": "@",
        "Ã": "ß",
        "Ã": "Ä",
        "Ã¤": "ä",
        "Ã¶": "ö",
        "Â°": "°",
        "Ã¿": "\x7f",
        "Ö³": "ó",
        "Ã": "Ö",
    }

    def iter_pages(self, previous_pages: Teletext) -> Generator[Tuple[int, int, Union[str, bool]], None, None]:
        for page_index in range(100, 900):

            url = f"https://teletext.zdf.de/php/options.php?mandant={self.ZDF_MANDANT}&site={page_index}"
            response = self.get_html(url)

            num_sub_pages, date = response.text.split(",")
            num_sub_pages = int(num_sub_pages) + 1

            page_status = {"date": date, "sub_pages": num_sub_pages}
            is_empty_page = date == "-1"

            # keep the files that don't have changed (according to published timestamp)
            #   and avoid downloading them because the pages include the current time
            previous_page = previous_pages.get_page(page_index)
            if previous_page:
                all_exist = False
                if not is_empty_page:
                    all_exist = all(
                        self.to_filename(page_index, sub_page_index + 1).exists()
                        for sub_page_index in range(num_sub_pages)
                    )
                    if all_exist:
                        for sub_page_index in range(num_sub_pages):
                            yield page_index, sub_page_index + 1, True
                if all_exist:
                    continue

            status[str(page_index)] = page_status

            if is_empty_page:
                continue

            for sub_page_index in range(num_sub_pages):
                page_name = f"{page_index}"
                if sub_page_index:
                    page_name = f"{page_name}_{sub_page_index}"

                url = f"https://teletext.zdf.de/teletext/{self.ZDF_MANDANT}/seiten/klassisch/{page_name}.html"
                response = self.get_html(url)

                if response.status_code == 200:
                    text = response.content.decode("utf-8")
                    yield page_index, sub_page_index + 1, text

        self.log("writing", status_filename)
        status_filename.write_text(json.dumps(status, indent=2))

    def to_teletext(self, content: str) -> TeletextPage:
        for wrong, correct in self.ENCODING_FIX_MAPPING.items():
            content = content.replace(wrong, correct)

        soup = self.to_soup(content)
        tt = TeletextPage()
        for row in soup.find("div", {"id": "content"}).find_all("div", {"class": "row"}):
            tt.new_line()

            for elem in row.find_all("span"):
                block = TeletextPage.Block(elem.text)

                classes = elem.get("class")
                if classes:
                    for cls in classes:
                        if cls.startswith("c"):
                            block.color = TeletextPage.rgb_to_teletext(cls[1:])
                        elif cls.startswith("bc"):
                            block.bg_color = TeletextPage.rgb_to_teletext(cls[2:])

                        elif cls == "teletextlinedrawregular":
                            # The codes they use are almost equivalent to g1
                            codes = [ord(c) for c in block.text]
                            block.text = ""
                            for c in codes:
                                if c >= 0xa0:
                                    # TODO: set block.char_set (which might require multiple blocks)
                                    c -= 0x80
                                if 0x20 <= c <= 0x3f or 0x60 <= c <= 0x7f:
                                    c = chr(TeletextPage.g1_to_unicode(c))
                                elif 0x41 == c:
                                    c = chr(TeletextPage.g1_to_unicode(0x7f))
                                elif 0xa0 == c:
                                    c = " "
                                else:
                                    # print(f"mhh {c:x}")
                                    c = "?"
                                block.text += c

                if block.text:
                    tt.add_block(block)

        return tt


class ZDF(ZDFBase):
    ABSTRACT = False
    NAME = "zdf"
    ZDF_MANDANT = "zdf"


class ZDFInfo(ZDFBase):
    ABSTRACT = False
    NAME = "zdf-info"
    ZDF_MANDANT = "zdfinfo"


class ZDFNeo(ZDFBase):
    ABSTRACT = False
    NAME = "zdf-neo"
    ZDF_MANDANT = "zdfneo"
