"""
Show significant words by using
the word-bags extracted with "extract.py"
"""
import math
from pathlib import Path
from typing import List

import pandas as pd

from src.words import TokenCounter


PROJECT_DIR: Path = Path(__file__).parent.parent
EXPORT_DIR: Path = PROJECT_DIR / "export" / "words"


def _normalize_token(key: str) -> str:
    return key.lower().replace("ß", "ss")


def dump_compare_channels(
        channels: List[str] = ("ntv", "ndr", "zdf", "ard"),
):
    tokens = {
        channel: {
            "all": TokenCounter.from_json(EXPORT_DIR / f"{channel}-all.json").map_key(_normalize_token),
            "doc": TokenCounter.from_json(EXPORT_DIR / f"{channel}-per-snapshot.json").map_key(_normalize_token),
        }
        for channel in channels
    }
    for channel1, tokens1 in tokens.items():
        for channel2, tokens2 in tokens.items():
            if channel1 != channel2:
                print(f"--- {channel1} vs {channel2}", "-" * 30)

                freq1 = tokens1["all"].to_freq() * tokens1["doc"].idf()
                freq2 = tokens2["all"].to_freq() * tokens2["doc"].idf()
                #freq1.dump(10, reverse=True)
                #continue
                diff = (freq1 - freq2 * 3).limited(0)
                diff.dump(10, reverse=True)


def dump_words_per_week(channel: str = "ntv"):
    weeks = [
        f"2022-{i}" for i in range(4, 9)
    ]
    print("-- all", "-"*20)
    tokens_all = TokenCounter.from_json(EXPORT_DIR / f"{channel}-all.json").map_key(_normalize_token)
    tokens_all.dump(10)
    print("-- doc", "-"*20)
    tokens_doc = TokenCounter.from_json(EXPORT_DIR / f"{channel}-per-page.json").map_key(_normalize_token)
    tokens_doc.dump(10)

    for week in weeks:
        print("--", week, "-"*20)

        tokens_week = TokenCounter.from_json(EXPORT_DIR / f"{channel}-{week}.json").map_key(_normalize_token)

        #tokens = tokens_week.to_freq() * tokens_all.idf()
        tokens = (tokens_week.to_freq() - tokens_all.to_freq() * 3.).limited(0)

        tokens.dump(10, reverse=True)




if __name__ == "__main__":
    #dump_compare_channels()
    dump_words_per_week()
