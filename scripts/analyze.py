from pathlib import Path

import pandas as pd

from src.iterator import TeletextIterator


PROJECT_DIR: Path = Path(__file__).parent.parent


def get_page_changes(tt_iterator: TeletextIterator) -> pd.DataFrame:
    rows = []

    previous_tt_map = {}
    for tt in tt_iterator.iter_teletexts():
        prev_tt = previous_tt_map.get(tt.channel)
        previous_tt_map[tt.channel] = tt

        if prev_tt:
            row = {
                "timestamp": tt.timestamp,
                "channel": tt.channel,
            }

            for index in set(prev_tt.page_index) | set(tt.page_index):
                prev_page = prev_tt.pages.get(index)
                page = tt.pages.get(index)
                row[f"{index[0]}-{index[1]:02}"] = page != prev_page

            rows.append(row)
            #if len(rows) > 3:
            #    break

    df = (
        pd.DataFrame(rows)
        .set_index(["timestamp", "channel"])
        .sort_index(axis=1)
    )
    print(df)
    return df


def main():
    tt_iterator = TeletextIterator(
#        channels=["ntv"],
    )
    df = get_page_changes(tt_iterator)
    df.to_csv(PROJECT_DIR / "export" / "pages-changed.csv")


if __name__ == "__main__":
    main()
