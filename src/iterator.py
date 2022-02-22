from pathlib import Path
from typing import Optional, Tuple, List, Iterable, Generator

from tqdm import tqdm

from .teletext import Teletext, TeletextPage
from .giterator import Giterator


class TeletextIterator:

    PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent

    def __init__(
            self,
            channels: Optional[Iterable[str]] = None,
            verbose: bool = True,
    ):
        self.channels: List[str] = [] if channels is None else list(channels)
        self.verbose = verbose
        self.git = Giterator(self.PROJECT_ROOT)

    def iter_teletexts(self) -> Generator[Teletext, None, None]:
        snapshot_path = "docs/snapshots"

        commit_iterable = self.git.iter_commits(snapshot_path)
        if self.verbose:
            commit_iterable = tqdm(
                commit_iterable,
                desc=f"commits",
                total=self.git.num_commits(snapshot_path),
            )

        for commit in commit_iterable:
            for file in commit.iter_files(snapshot_path):
                name = file.name.split("/")[-1]
                if not name.endswith(".ndjson"):
                    continue

                channel = name.split(".")[0]
                if self.channels and channel not in self.channels:
                    continue

                tt = Teletext.from_ndjson(file.data, ignore_errors=True)
                tt.commit_hash = commit.hash
                yield tt
