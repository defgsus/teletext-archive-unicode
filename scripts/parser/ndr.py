import re
import datetime
from typing import List, Iterable

import dateutil.parser

from src.teletext import Teletext, TeletextPage
from .base import TeletextParserBase


class NdrParser(TeletextParserBase):
    channels = ("ndr",)

    _RE_DATE = [
        re.compile(r"\s*(\d+). (\w+) (\d\d\d\d)\s+Stand: (\d+):(\d\d)"),
        re.compile(r"\s*Stand:\s+(\d+). (\w+) (\d\d\d\d)\s+(\d+):(\d\d)")
    ]
    def parse_buckets_675_679(self, page: TeletextPage):
        """
        Air quality
        """
        lines = self.page_to_lines(page)
        timestamp = None
        for re_date in self._RE_DATE:
            for line in lines[7:9]:
                try:
                    match = re_date.match(line).groups()
                    timestamp = datetime.datetime(
                        int(match[2]),
                        self.GERMAN_MONTH_NAMES.index(match[1]) + 1,
                        int(match[0].lstrip("0")),
                        int(match[3].lstrip("0") or 0),
                        int(match[4].lstrip("0") or 0),
                    ).isoformat()
                    break
                except Exception as e:
                    pass
        if not timestamp:
            print(f"Can't parse ndr {page.timestamp} {page.index}-{page.sub_index} date: {lines[7:9]}")

        for line in self.split_lines_vertical(
                lines[11:22], 22 if page.index in (676, 677) else 20, 27, 34
        ):
            city = line[0].strip()
            if not city:
                continue
            if city.startswith("Weitere Info") or city.startswith("www.luft.sch") or city.startswith("Internet:"):
                continue
            if city.endswith(" k"):
                city = city[:-1].rstrip()

            for index, name in ((
                    (1, "ozon"),
                    (2, "no2"),
                    (3, "pm10"),
            )):
                try:
                    self.add_bucket(
                        timestamp,
                        ("ndr", f"air_{name}", city),
                        int(line[index].lstrip(" <"))
                    )
                except Exception as e:
                    if line[index].strip() not in ("-", "--", "k.A.", ".A."):
                        print(f"Can't parse ndr {page.timestamp} {page.index}-{page.sub_index} air-{name}: [{line}], {type(e).__name__}: {e}")
