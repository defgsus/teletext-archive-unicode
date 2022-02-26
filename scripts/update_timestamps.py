"""
Little script for updating `docs/snapshots/_timestamps.ndjson`

It builds an index of the commit hashes and actual snapshot timestamps.
"""
import json
from pathlib import Path
from src.iterator import TeletextIterator


TIMESTAMPS_FILENAME: Path = Path(__file__).resolve().parent.parent / "docs/snapshots/_timestamps.ndjson"


def update_timestamps_all():
    """Rebuild the complete file"""
    with open(str(TIMESTAMPS_FILENAME), "w") as fp:
        for timestamp, hash in sorted(
                TeletextIterator().iter_commit_timestamps(),
                key=lambda th: th[0]
        ):
            print(json.dumps({"timestamp": timestamp, "hash": hash}), file=fp)


def update_timestamps():
    """Add newest commits to end of file"""
    if not TIMESTAMPS_FILENAME.exists():
        update_timestamps_all()
        return

    existing_timestamps = TIMESTAMPS_FILENAME.read_text().splitlines()
    latest_timestamp = json.loads(existing_timestamps[-1])

    with open(str(TIMESTAMPS_FILENAME), "a") as fp:

        for timestamp, hash in sorted(
                TeletextIterator().iter_commit_timestamps(
                    after_hash=latest_timestamp["hash"]
                ),
                key=lambda th: th[0]
        ):
            print(json.dumps({"timestamp": timestamp, "hash": hash}), file=fp)


if __name__ == "__main__":
    update_timestamps()
