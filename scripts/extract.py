import os
import datetime
from pathlib import Path

import pandas as pd

from src.iterator import TeletextIterator
from src.words import TokenCounter


PROJECT_DIR: Path = Path(__file__).parent.parent
EXPORT_DIR: Path = PROJECT_DIR / "export"


def export_page_changes(tt_iterator: TeletextIterator) -> pd.DataFrame:
    rows = []

    previous_tt_map = {}
    for tt in tt_iterator.iter_teletexts():
        prev_tt = previous_tt_map.get(tt.channel)
        previous_tt_map[tt.channel] = tt

        if prev_tt:
            row = {
                "timestamp": tt.timestamp[:17] + "00",
                "channel": tt.channel,
            }

            for index in set(prev_tt.page_index) | set(tt.page_index):
                prev_page = prev_tt.pages.get(index)
                page = tt.pages.get(index)

                if prev_page is not None and page is not None:
                    equal = page.lines[1:] == prev_page.lines[1:]
                else:
                    equal = page == prev_page

                row[f"{index[0]}-{index[1]:02}"] = 0. if equal else 1.

            rows.append(row)

    df = (
        pd.DataFrame(rows)
        .set_index(["timestamp", "channel"])
        .sort_index(axis=1)
    )
    print(df)
    os.makedirs(EXPORT_DIR, exist_ok=True)
    df.to_csv(EXPORT_DIR / "pages-changed.csv")
    return df


def export_token_counts(tt_iterator: TeletextIterator) -> pd.DataFrame:
    export_dir = EXPORT_DIR / "words"
    os.makedirs(export_dir, exist_ok=True)

    channel_counters = dict()

    prev_date_key = None
    for tt in tt_iterator.iter_teletexts():
        date_key = "%s-%s" % (
            datetime.datetime.strptime(tt.timestamp[:10], "%Y-%m-%d").isocalendar()[:2]
        )

        if tt.channel not in channel_counters:
            channel_counters[tt.channel] = {
                "all": TokenCounter(),
                "all_page": TokenCounter(),
                "all_snapshot": TokenCounter(),
                "date": TokenCounter(),
            }

        if prev_date_key and prev_date_key != date_key:
            for channel, counters in channel_counters.items():
                counters["date"].to_json(export_dir / f"{channel}-{prev_date_key}.json")
                counters["date"] = TokenCounter()

        counters = channel_counters[tt.channel]

        snapshot_tokens = set()
        for index, page in tt.pages.items():
            tokens = page.to_tokens()
            counters["all"].add(*tokens)
            counters["date"].add(*tokens)
            token_set = set(tokens)
            counters["all_page"].add(*token_set)
            snapshot_tokens |= token_set

        counters["all_snapshot"].add(*snapshot_tokens)

        prev_date_key = date_key

    for channel, counters in channel_counters.items():
        counters["date"].to_json(export_dir / f"{channel}-{prev_date_key}.json")
        counters["all"].to_json(export_dir / f"{channel}-all.json")
        counters["all_page"].to_json(export_dir / f"{channel}-per-page.json")
        counters["all_snapshot"].to_json(export_dir / f"{channel}-per-snapshot.json")



def main():
    tt_iterator = TeletextIterator(
#        channels=["ntv"],
    )
    #export_page_changes(tt_iterator)
    export_token_counts(tt_iterator)


if __name__ == "__main__":
    main()
