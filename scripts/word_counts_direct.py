import os
import datetime
from pathlib import Path
from typing import List

import pandas as pd

from src.iterator import TeletextIterator
from src.words import TokenCounter


PROJECT_DIR: Path = Path(__file__).parent.parent
EXPORT_DIR: Path = PROJECT_DIR / "export"


def export_token_counts(
        tt_iterator: TeletextIterator,
        token_filter: List[str],
) -> pd.DataFrame:
    token_filter = set(token_filter)

    export_dir = EXPORT_DIR
    os.makedirs(export_dir, exist_ok=True)

    rows = []

    for tt in tt_iterator.iter_teletexts():

        counters = {
            "all": TokenCounter(),
            "page": TokenCounter(),
            "snapshot": TokenCounter(),
        }

        snapshot_tokens = set()
        for index, page in tt.pages.items():
            tokens = page.to_tokens(lowercase=True)
            tokens = [t for t in tokens if t in token_filter]

            counters["all"].add(*tokens)
            token_set = set(tokens)
            counters["page"].add(*token_set)
            snapshot_tokens |= token_set

        counters["snapshot"].add(*snapshot_tokens)

        for key, counter in counters.items():
            row = {
                "timestamp": tt.timestamp,
                "channel": tt.channel,
                "key": key,
            }
            for token, value in counter.tokens.items():
                row[token] = value
                row[f"freq_{token}"] = counter.freq_of(token)

            rows.append(row)

    df = pd.DataFrame(rows).set_index(["timestamp", "channel", "key"])
    df.to_csv(export_dir / "special-word-counts.csv")
    print(df)


def main():
    tt_iterator = TeletextIterator(
#        channels=["ntv"],
    )
    export_token_counts(
        tt_iterator,
        token_filter=["ukraine", "russland", "corona", "krieg", "propaganda", "virus", "pandemie"],
    )


if __name__ == "__main__":
    main()
