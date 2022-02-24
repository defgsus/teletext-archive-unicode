import json
from pathlib import Path
from src.iterator import TeletextIterator


def update_timestamps():
    with open(Path(__file__).resolve().parent.parent / "docs/snapshots/_timestamps.ndjson", "w") as fp:
        for timestamp, hash in sorted(
                TeletextIterator().iter_commit_timestamps(),
                key=lambda th: th[0]
        ):
            print(json.dumps({"timestamp": timestamp, "hash": hash}), file=fp)


if __name__ == "__main__":
    update_timestamps()
