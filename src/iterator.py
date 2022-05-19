import json
import tarfile
from pathlib import Path
from typing import Optional, Tuple, List, Iterable, Generator

from tqdm import tqdm

from .teletext import Teletext, TeletextPage
from .giterator import Giterator


class TeletextIterator:
    """
    Access to Teletext instances throughout the git history
    """

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

    def iter_teletexts(
            self,
            after_hash: Optional[str] = None,
    ) -> Generator[Teletext, None, None]:

        commit_iterable = self.git.iter_commits(self.SNAPSHOT_PATH)
        if self.verbose:
            commit_iterable = tqdm(
                commit_iterable,
                desc=f"commits",
                total=self.git.num_commits(self.SNAPSHOT_PATH),
            )

        yield_files = after_hash is None

        for commit in commit_iterable:

            if yield_files:
                for file in commit.iter_files(self.SNAPSHOT_PATH):
                    name = file.name.split("/")[-1]
                    if not name.endswith(".ndjson") or name.startswith("_"):
                        continue

                    channel = name.split(".")[0]
                    if self.channels and channel not in self.channels:
                        continue

                    tt = Teletext.from_ndjson(file.data)
                    tt.commit_hash = commit.hash
                    yield tt

            if after_hash and commit.hash.startswith(after_hash):
                yield_files = True

    def iter_commit_timestamps(self, after_hash: Optional[str] = None) -> Generator[Tuple[str, str], None, None]:
        """
        Yields the timestamp and the hash of each data commit
        """
        yield_commits = after_hash is None
        for commit in self.git.iter_commit_hashes(f"{self.SNAPSHOT_PATH}/zdf.ndjson"):
            if yield_commits:
                file = list(self.git.iter_files(commit["hash"], [f"{self.SNAPSHOT_PATH}/zdf.ndjson"]))[0]
                header = json.loads(file.data.decode("utf-8").split("\n", 1)[0])
                yield header["timestamp"], commit["hash"]

            if after_hash and commit["hash"].startswith(after_hash):
                yield_commits = True

    def get_historic_teletext(self, channel: str, commit_hash: str) -> Optional[Teletext]:
        try:
            files = list(self.git.iter_files(commit_hash, [f"docs/snapshots/{channel}.ndjson"]))
        except tarfile.ReadError:
            return
        if files:
            tt = Teletext.from_ndjson(files[0].data)
            tt.commit_hash = commit_hash
            return tt

