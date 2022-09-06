import re
import datetime
from typing import List, Iterable

import dateutil.parser

from src.teletext import Teletext, TeletextPage
from .base import TeletextParserBase


class NtvParser(TeletextParserBase):
    channels = ("ntv",)

    def parse_buckets_497(self, page: TeletextPage):
        """
        Oil prices
        """
        lines = self.page_to_lines(page)

        for line in lines[7:18]:
            line = line.strip().split()
            if not line:
                print(f"Can't parse ntv {page.timestamp} {page.index}-{page.sub_index}: empty line")
                continue

            city = line[0]

            for index, name in ((
                    (1, "oil_price_low"),
                    (3, "oil_price_high"),
                    (4, "oil_price"),
            )):
                try:
                    self.add_bucket(
                        page.timestamp,
                        ("ntv", name, city),
                        float(line[index].replace(",", "."))
                    )
                except Exception as e:
                    print(f"Can't parse ntv {page.timestamp} {page.index}-{page.sub_index} {name}: [{line}], {type(e).__name__}: {e}")

    def parse_buckets_499(self, page: TeletextPage):
        """
        Phone prices
        """
        lines = self.page_to_lines(page)
        try:
            timestamp = (
                dateutil.parser.parse(page.timestamp)
                .replace(
                    hour=int(lines[6].lstrip()[:2].lstrip("0") or 0),
                    minute=0,
                    second=0,
                )
            ).isoformat()
        except Exception as e:
            print(f"Can't parse ntv {page.timestamp} {page.index}-{page.sub_index} timestamp: [{lines[6]}], {type(e).__name__}: {e}")
            return

        for line_index, name in ((
                (10, "city"),
                (14, "country"),
                (18, "mobile"),
        )):
            line = lines[line_index]
            for i, x in enumerate((15, 27)):
                try:
                    self.add_bucket(
                        timestamp,
                        ("ntv", f"phone_price_{i+1}", name),
                        float(line[x:x+5].replace(",", ".")),
                    )
                except Exception as e:
                    print(f"Can't parse ntv {page.timestamp} {page.index}-{page.sub_index} phone_price {name}: [{line}], {type(e).__name__}: {e}")
