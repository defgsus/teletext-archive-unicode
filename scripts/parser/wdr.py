import re
import datetime
from typing import List, Iterable

from src.teletext import Teletext, TeletextPage
from .base import TeletextParserBase


class WdrParser(TeletextParserBase):
    channels = ("wdr",)

    _RE_WDR_DATE = re.compile(r"\s*Daten vom ([\d]+). ([\w]+), (\d+):(\d\d) Uhr")
    _RE_WDR_PREV_TEMP = re.compile(r"\s*([\s\w/'.\-]+)\s+(-?\d+)°C\s+(-?\d+)°C\s+([\d,]+)\s+mm")
    _RE_WDR_TEMP = re.compile(r"\s*([\s\w/'.\-]+)\s+(-?\d+)°C\s+([\w\s]+)")
    _RE_WDR_PRESSURE = re.compile(r"\s*([\s\w/'.\-]+)\s+(\d+)\shPa")
    _RE_WDR_WIND = re.compile(r"\s*([\s\w/'.\-]+)\s+([A-Z]+)\s+(\d+)\s+([\d,]+)\s+(\d+|-)")
    _RE_WDR_WATER_LEVEL = re.compile(r"\s*([\s\w/'.\-]+)\s+(\d+).(\d\d)\s+(\d\d):(\d\d)\s+([\d]+)")

    def parse_buckets_183(self, page: TeletextPage):
        lines = self.page_to_lines(page)
        for line in lines[11:21]:
            match = self._RE_WDR_PREV_TEMP.match(line)
            try:
                values = match.groups()
                city = values[0].strip()
                self.add_bucket(page.timestamp, ("wdr", "prev_temp_high", city), int(values[1]))
                self.add_bucket(page.timestamp, ("wdr", "prev_temp_low", city), int(values[2]))
                self.add_bucket(page.timestamp, ("wdr", "prev_rain", city), float(values[3].replace(",", ".")))
            except Exception as e:
                print(f"Can't parse wdr {page.timestamp} 183 temp: [{line}], {type(e).__name__}: {e}")

    def parse_buckets_184(self, page: TeletextPage):
        lines = self.page_to_lines(page)
        try:
            match = self._RE_WDR_DATE.match(lines[6]).groups()
            weather_date = datetime.datetime(
                int(page.timestamp[:4]),
                self.GERMAN_MONTH_NAMES.index(match[1]) + 1,
                int(match[0]),
                int(match[2]),
                int(match[3]),
            ).isoformat()
        except Exception as e:
            print(f"Can't parse wdr {page.timestamp} 184 date: [{lines[6]}], {type(e).__name__}: {e}")
            return

        for line in lines[8:18]:
            match = self._RE_WDR_TEMP.match(line)
            try:
                values = match.groups()
                city = values[0].strip()
                self.add_bucket(weather_date, ("wdr", "temp", city), int(values[1]))
                self.add_bucket(weather_date, ("wdr", "coverage", city), values[2].strip())
            except Exception as e:
                print(f"Can't parse wdr {page.timestamp} 184 temp: [{line}], {type(e).__name__}: {e}")

        for line in lines[20:22]:
            try:
                values = self._RE_WDR_PRESSURE.match(line).groups()
                city = values[0].strip()
                self.add_bucket(weather_date, ("wdr", "pressure", city), int(values[1]))
            except Exception as e:
                print(f"Can't parse wdr {page.timestamp} 184 pressure: [{line}], {type(e).__name__}: {e}")

    def parse_buckets_185(self, page: TeletextPage):
        lines = self.page_to_lines(page)
        try:
            match = self._RE_WDR_DATE.match(lines[6]).groups()
            weather_date = datetime.datetime(
                int(page.timestamp[:4]),
                self.GERMAN_MONTH_NAMES.index(match[1]) + 1,
                int(match[0]),
                int(match[2]),
                int(match[3]),
            ).isoformat()
        except Exception as e:
            print(f"Can't parse wdr {page.timestamp} 185 date: [{lines[6]}], {type(e).__name__}: {e}")
            return

        for line in lines[10:20]:
            match = self._RE_WDR_WIND.match(line)
            try:
                values = match.groups()
                city = values[0].strip()
                self.add_bucket(weather_date, ("wdr", "wind_dir", city), values[1])
                self.add_bucket(weather_date, ("wdr", "wind_speed", city), int(values[2]))
                self.add_bucket(weather_date, ("wdr", "rain", city), float(values[3].replace(",", ".")))
                if values[4] != "-":
                    self.add_bucket(weather_date, ("wdr", "sun", city), int(values[4]))
            except Exception as e:
                print(f"Can't parse wdr {page.timestamp} 185 wind: [{line}], {type(e).__name__}: {e}")

    def parse_buckets_190(self, page: TeletextPage):
        lines = self.page_to_lines(page)
        for line in lines[6:21 if page.sub_index < 3 else 19]:
            if not line.strip():
                continue
            match = self._RE_WDR_WATER_LEVEL.match(line)
            try:
                values = match.groups()
                name = values[0].strip()
                level_date = datetime.datetime(
                    int(page.timestamp[:4]),
                    int(values[2].lstrip("0")),
                    int(values[1].lstrip("0")),
                    int(values[3].lstrip("0") or 0),
                    int(values[4].lstrip("0") or 0),
                ).isoformat()

                self.add_bucket(level_date, ("wdr", "water_level", name), int(values[5]))
            except Exception as e:
                print(f"Can't parse wdr {page.timestamp} 190-{page.sub_index} water-level: [{line}], {type(e).__name__}: {e}")
