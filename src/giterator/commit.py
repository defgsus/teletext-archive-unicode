import datetime
from typing import List, Optional, Generator, TextIO

from .file import File
from .helper import safe_console_string


class Commit:

    def __init__(
            self,
            repo: 'GitRepo',
            hash: str,
            tree_hash: str,
            parent_hash: List[str],
            author: str,
            author_email: str,
            author_date: datetime.datetime,
            committer: str,
            committer_email: str,
            committer_date: datetime.datetime,
            encoding: str,
            message: str,
            ref_names: Optional[List[str]] = None,
            changes: Optional[List[dict]] = None,
    ):
        from .giterator import Giterator
        self.repo: Giterator = repo
        self.hash: str = hash
        self.tree_hash = tree_hash
        self.parent_hash = parent_hash or []
        self.author = author
        self.author_email = author_email
        self.author_date = author_date
        self.committer = committer
        self.committer_email = committer_email
        self.committer_date = committer_date
        self.encoding = encoding
        self.message = message
        self.ref_names = ref_names or []
        self.changes = changes or []

    def __repr__(self):
        #param = f"'{self.hash}'"
        param = ", ".join(
            f"{key}={repr(value)}"
            for key, value in self.to_dict().items()
        )
        return f"{self.__class__.__name__}({param})"

    def __hash__(self):
        return int(self.hash, base=16)

    def to_dict(self):
        return {
            "hash": self.hash,
            "tree_hash": self.tree_hash,
            "parent_hash": self.parent_hash,
            "author": self.author,
            "author_email": self.author_email,
            "author_date": self.author_date,
            "committer": self.committer,
            "committer_email": self.committer_email,
            "committer_date": self.committer_date,
            "encoding": self.encoding,
            "message": self.message,
            "ref_names": self.ref_names,
            "changes": self.changes,
        }

    def iter_files(self, *filenames: str) -> Generator[File, None, None]:
        """
        Iterate through **all** or specific files in the repo at the state of this commit
        :return: generator of File
        """
        yield from self.repo.iter_files(self.hash, filenames=list(filenames))

    def iter_commit_files(self) -> Generator[File, None, None]:
        """
        Iterate through all files that have been created, changed or renamed by this
        commit.

        Does not include deleted files.

        :return: generator of File
        """
        if self.changes:
            filenames = []
            for ch in self.changes:
                if ch["type"] != "delete":
                    filenames.append(ch["name"])

            if filenames:
                yield from self.iter_files(*filenames)

    def dump(self, file: TextIO = None):
        commit = self
        print("hash:       ", commit.hash, file=file)
        print("tree_hash:  ", commit.tree_hash, file=file)
        print("parent_hash:", ", ".join(commit.parent_hash), file=file)
        print("ref_names:  ", ", ".join(commit.ref_names), file=file)
        print(f"author:      {safe_console_string(commit.author)} "
              f"<{safe_console_string(commit.author_email)}> "
              f"@ {commit.author_date.isoformat()}", file=file)
        print(f"committer:   {safe_console_string(commit.committer)} "
              f"<{safe_console_string(commit.committer_email)}> "
              f"@ {commit.committer_date.isoformat()}", file=file)
        print("encoding:   ", commit.encoding, file=file)
        print(f"message:     ```{safe_console_string(commit.message)}```", file=file)

        if commit.changes:
            print("changes:", file=file)
            for ch in commit.changes:
                s = f"  {ch['type']} +{ch['additions']:5} -{ch['deletions']:5}"
                if ch["type"] == "rename":
                    s += f" {ch['old_name']} => {ch['name']}"
                else:
                    s += f" {ch['name']}"

                print(s, file=file)
