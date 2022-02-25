import json
import tarfile
from pathlib import Path
from typing import Optional, Tuple, List, Iterable, Generator

from tqdm import tqdm

from .teletext import Teletext, TeletextPage
from .giterator import Giterator


class TeletextIterator:

    PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
    SNAPSHOT_PATH = "docs/snapshots"

    def __init__(
            self,
            channels: Optional[Iterable[str]] = None,
            verbose: bool = True,
    ):
        self.channels: List[str] = [] if channels is None else list(channels)
        self.verbose = verbose
        self.git = Giterator(self.PROJECT_ROOT)

    def iter_teletexts(self) -> Generator[Teletext, None, None]:

        commit_iterable = self.git.iter_commits(self.SNAPSHOT_PATH)
        if self.verbose:
            commit_iterable = tqdm(
                commit_iterable,
                desc=f"commits",
                total=self.git.num_commits(self.SNAPSHOT_PATH),
            )

        for commit in commit_iterable:
            for file in commit.iter_files(self.SNAPSHOT_PATH):
                name = file.name.split("/")[-1]
                if not name.endswith(".ndjson") or name.startswith("_"):
                    continue

                channel = name.split(".")[0]
                if self.channels and channel not in self.channels:
                    continue

                tt = Teletext.from_ndjson(file.data, ignore_errors=True)
                tt.commit_hash = commit.hash
                yield tt

    def iter_commit_timestamps(self) -> Generator[Tuple[str, str], None, None]:
        """
        Yields the timestamp and the hash of each data commit
        """
        for commit in self.git.iter_commit_hashes(f"{self.SNAPSHOT_PATH}/zdf.ndjson"):
            file = list(self.git.iter_files(commit["hash"], [f"{self.SNAPSHOT_PATH}/zdf.ndjson"]))[0]
            header = json.loads(file.data.decode("utf-8").split("\n", 1)[0])
            yield header["timestamp"], commit["hash"]

    def get_historic_teletext(self, channel: str, commit_hash: str) -> Optional[Teletext]:
        try:
            files = list(self.git.iter_files(commit_hash, [f"docs/snapshots/{channel}.ndjson"]))
        except tarfile.ReadError:
            return
        if files:
            tt = Teletext.from_ndjson(files[0].data, ignore_errors=True)
            tt.commit_hash = commit_hash
            return tt

