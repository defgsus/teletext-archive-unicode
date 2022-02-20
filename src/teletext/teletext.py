import json
from pathlib import Path
from typing import List, Optional, TextIO, Tuple, Union

from .page import TeletextPage


class Teletext:
    
    def __init__(self):
        self.pages = {}
        self.page_index = []
        self.timestamp = None
        
    @classmethod
    def from_ndjson(cls, filename: Union[str, Path]) -> "Teletext":
        tt = cls()
        lines = Path(filename).read_text().strip().splitlines()
        
        cur_page = None
        for line in lines:
            line = json.loads(line)
            if isinstance(line, dict):
                # file header
                if "scraper" in line:
                    tt.timestamp = line["timestamp"]
                    continue

                cur_page = TeletextPage()
                cur_page.index = line["page"]
                cur_page.sub_index = line["sub_page"]
                cur_page.timestamp = line["timestamp"]
                cur_page.error = line.get("error")
                index = (cur_page.index, cur_page.sub_index)
                tt.pages[index] = cur_page
                tt.page_index.append(index)
            else:
                assert cur_page, f"line before page"
                cur_page.lines.append([
                    TeletextPage.Block.from_json(block)
                    for block in line
                ])
        
        tt.page_index.sort()
        return tt

    def get_page(self, page: int, sub_page: Optional[int] = None) -> Optional[TeletextPage]:
        if sub_page is not None:
            return self.pages.get((page, sub_page))
        for key in self.page_index:
            if key[0] == page:
                return self.pages[key]

    def get_next_page(self, page: int, sub_page: int, dir: int = 1) -> Tuple[int, int]:
        page = page, sub_page
        if dir == 0:
            for p in self.page_index:
                if p >= page:
                    return p
            return self.page_index[0]

        if dir > 0:
            for p in self.page_index:
                if p > page:
                    return p
            return self.page_index[0]

        elif dir < 0:
            for p in reversed(self.page_index):
                if p < page:
                    return p
            return self.page_index[-1]

        return page
