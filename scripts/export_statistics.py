"""
Export all the tele-text-published statistical data
"""
import json
import re
import datetime
import sys
from pathlib import Path
from typing import Tuple, Union

import dateutil.parser
import pandas as pd
import numpy as np

from src.iterator import TeletextIterator, Teletext, TeletextPage
from scripts.parser import TeletextParserBase


class StatisticsExporter:

    def __init__(self, tt_iterator: TeletextIterator):
        self.tt_iterator = tt_iterator
        self.buckets = {}
        self.parsers = [
            c(self)
            for c in TeletextParserBase.registered_classes.values()
        ]

    def run(self):
        for tt in self.tt_iterator.iter_teletexts():
            for parser in self.parsers:
                if tt.channel in parser.channels:
                    parser.parse_buckets(tt)

    def add_bucket(self, timestamp: str, key: Union[str, Tuple[str, ...]], value):
        if not isinstance(key, str):
            key = "|".join(key)

        if timestamp not in self.buckets:
            self.buckets[timestamp] = {}

        self.buckets[timestamp][key] = value

    def add_bucket_XXX(self, timestamp: str, key: Union[str, Tuple[str, ...]], value):
        if not isinstance(key, tuple):
            key = (key, )

        bucket = self.buckets
        for k in key:
            if k not in bucket:
                bucket[k] = {}
            bucket = bucket[k]

        bucket[timestamp] = value


def main():
    buckets_file = Path("./statistics_buckets.json")

    if not buckets_file.exists() or "-f" in sys.argv:
        tt_iterator = TeletextIterator(
            verbose=True,
            channels=[
                "wdr",
                "ndr",
                "ntv",
            ],
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

    buckets = json.loads(buckets_file.read_text())
    df = pd.DataFrame(buckets)
    print(df)


if __name__ == "__main__":
    main()
