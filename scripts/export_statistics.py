"""
Export all the tele-text-published statistical data
"""
import json
import re
import datetime
from pathlib import Path
from typing import Tuple, Union

import dateutil.parser

from src.iterator import TeletextIterator, Teletext, TeletextPage

class StatisticsExporter:
    _MONTH_NAMES = [
        "Januar", "Februar", "März", "April", "Mai", "Juni", "Juli",
        "August", "September", "Oktober", "November", "Dezember",
    ]
    _RE_WDR_DATE = re.compile(r"\s*Daten vom ([\d]+). ([\w]+), (\d+):(\d\d) Uhr")
    _RE_WDR_PREV_TEMP = re.compile(r"\s*([\s\w/'.\-]+)\s+(-?\d+)°C\s+(-?\d+)°C\s+([\d,]+)\s+mm")
    _RE_WDR_TEMP = re.compile(r"\s*([\s\w/'.\-]+)\s+(-?\d+)°C\s+([\w\s]+)")
    _RE_WDR_PRESSURE = re.compile(r"\s*([\s\w/'.\-]+)\s+(\d+)\shPa")
    _RE_WDR_WIND = re.compile(r"\s*([\s\w/'.\-]+)\s+([A-Z]+)\s+(\d+)\s+([\d,]+)\s+(\d+|-)")

    def __init__(self, tt_iterator: TeletextIterator):
        self.tt_iterator = tt_iterator
        self.buckets = {}

    def run(self):
        for tt in self.tt_iterator.iter_teletexts():
            if tt.channel == "wdr":
                self.scan_wdr(tt)

    def add_bucket(self, timestamp: str, key: Union[str, Tuple[str, ...]], value):
        if not isinstance(key, tuple):
            key = (key, )

        bucket = self.buckets
        for k in key:
            if k not in bucket:
                bucket[k] = {}
            bucket = bucket[k]

        bucket[timestamp] = value

    def scan_wdr(self, tt: Teletext):
        # -- last day's low/high temp --
        page = tt.get_page(183)
        if not page:
            print(f"wdr {tt.timestamp} page 183 missing")
        else:
            lines = page.to_ansi(colors=False).replace("\xa0", " ").splitlines()
            for line in lines[11:21]:
                match = self._RE_WDR_PREV_TEMP.match(line)
                try:
                    values = match.groups()
                    city = values[0].strip()
                    self.add_bucket(page.timestamp, ("wdr", "prev_temp_high", city), int(values[1]))
                    self.add_bucket(page.timestamp, ("wdr", "prev_temp_low", city), int(values[2]))
                    self.add_bucket(page.timestamp, ("wdr", "prev_rain", city), float(values[3].replace(",", ".")))
                except Exception as e:
                    print(f"Can't parse wdr {tt.timestamp} 183 temp: [{line}], {type(e).__name__}: {e}")

        # -- today's temp --
        page = tt.get_page(184)
        if not page:
            print(f"wdr {tt.timestamp} page 184 missing")
        else:
            lines = page.to_ansi(colors=False).replace("\xa0", " ").splitlines()
            try:
                match = self._RE_WDR_DATE.match(lines[6]).groups()
                weather_date = datetime.datetime(
                    int(tt.timestamp[:4]),
                    self._MONTH_NAMES.index(match[1]) + 1,
                    int(match[0]),
                    int(match[2]),
                    int(match[3]),
                ).isoformat()
            except Exception as e:
                print(f"Can't parse wdr {tt.timestamp} 184 date: [{lines[6]}], {type(e).__name__}: {e}")
                weather_date = None

            if weather_date:
                for line in lines[8:18]:
                    match = self._RE_WDR_TEMP.match(line)
                    try:
                        values = match.groups()
                        city = values[0].strip()
                        self.add_bucket(weather_date, ("wdr", "temp", city), int(values[1]))
                        self.add_bucket(weather_date, ("wdr", "coverage", city), values[2].strip())
                    except Exception as e:
                        print(f"Can't parse wdr {tt.timestamp} 184 temp: [{line}], {type(e).__name__}: {e}")

                for line in lines[20:22]:
                    try:
                        values = self._RE_WDR_PRESSURE.match(line).groups()
                        city = values[0].strip()
                        self.add_bucket(weather_date, ("wdr", "pressure", city), int(values[1]))
                    except Exception as e:
                        print(f"Can't parse wdr {tt.timestamp} 184 pressure: [{line}], {type(e).__name__}: {e}")

        # -- today's wind --
        page = tt.get_page(185)
        if not page:
            print(f"wdr {tt.timestamp} page 185 missing")
        else:
            lines = page.to_ansi(colors=False).replace("\xa0", " ").splitlines()
            try:
                match = self._RE_WDR_DATE.match(lines[6]).groups()
                weather_date = datetime.datetime(
                    int(tt.timestamp[:4]),
                    self._MONTH_NAMES.index(match[1]) + 1,
                    int(match[0]),
                    int(match[2]),
                    int(match[3]),
                    ).isoformat()
            except Exception as e:
                print(f"Can't parse wdr {tt.timestamp} 185 date: [{lines[6]}], {type(e).__name__}: {e}")
                weather_date = None

            if weather_date:
                for line in lines[10:20]:
                    match = self._RE_WDR_WIND.match(line)
                    try:
                        values = match.groups()
                        city = values[0].strip()
                        self.add_bucket(weather_date, ("wdr", "wind_dir", city), values[1])
                        self.add_bucket(weather_date, ("wdr", "wind_speed", city), int(values[2]))
                        self.add_bucket(weather_date, ("wdr", "rain2", city), float(values[3].replace(",", ".")))
                        if values[4] != "-":
                            self.add_bucket(weather_date, ("wdr", "sun", city), int(values[4]))
                    except Exception as e:
                        print(f"Can't parse wdr {tt.timestamp} 185 wind: [{line}], {type(e).__name__}: {e}")

def main():
    buckets_file = Path("./statistics_buckets.json")

    tt_iterator = TeletextIterator(
        verbose=True,
        channels=["wdr"],
    )
    exporter = StatisticsExporter(tt_iterator)
    try:
        exporter.run()
        buckets_file.write_text(json.dumps(exporter.buckets, ensure_ascii=False))
    except KeyboardInterrupt:
        try:
            answer = input(f"still write {buckets_file}? ")
            if answer in ("y", "Y"):
                buckets_file.write_text(json.dumps(exporter.buckets, ensure_ascii=False))
        except KeyboardInterrupt:
            print()

if __name__ == "__main__":
    main()
