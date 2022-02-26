import re
import sys
import tarfile
import subprocess
from pathlib import Path
from io import BytesIO, StringIO
from typing import Generator, List, Tuple, Optional, Sequence, Union

from .helper import parse_datetime, decode, get_git_renaming
from .commit import Commit
from .file import File


class Giterator:
    RE_CHANGE_NUMSTATS = re.compile(r"^(-|\d+)\s(-|\d+)\s(.*)$")
    RE_CHANGE_SUMMARY = re.compile(r"^([a-z]+) mode (\d\d\d\d\d\d) (.+)")
    MAX_TOKEN_LENGTH = 64
    LOG_INFOS = [
        ("%H", "hash"),
        ("%T", "tree_hash"),
        ("%P", "parent_hash", lambda s: s.split() if s.strip() else []),
        ("%an", "author"),
        ("%ae", "author_email"),
        ("%aI", "author_date", parse_datetime),
        ("%an", "committer"),
        ("%ae", "committer_email"),
        ("%aI", "committer_date", parse_datetime),
        ("%D", "ref_names", lambda s: s.split(", ") if s.strip() else []),
        ("%e", "encoding"),
    ]
    # something that should never appear in a git message
    DELIMITER1 = "$$$1-GiTeRaToR-dAtA-dElImItEr-$$$"
    DELIMITER2 = "\n$$$2-GiTeRaToR-dAtA-dElImItEr-$$$"

    def __init__(
            self,
            path: Union[str, Path],
            git_args: List[str] = None,
            verbose: bool = False,
    ):
        self.verbose = verbose
        self.path = str(path)
        self._git_args = git_args or []
        self._num_commits = None
        self._hashes = set()

    def _log(self, *args):
        if self.verbose:
            print(*args, file=sys.stderr)

    def num_commits(self, *filenames: str, all: bool = False) -> int:
        if self._num_commits is None:
            args = ["git", "rev-list", "--count"] + self._git_args
            if all:
                if "--all" not in self._git_args:
                    args.append("--all")
            else:
                if "--branches" not in self._git_args:
                    args.append("--branches")

            if filenames:
                args += ["--"] + list(filenames)

            self._log(" ".join(args))
            output = subprocess.check_output(args, cwd=self.path)
            self._num_commits = int(output)

        return self._num_commits

    def first_commit(self, *filenames: Union[str, Path]) -> Optional[Commit]:
        for commit in self.iter_commits(*filenames, reverse=False):
            return commit

    def last_commit(self, *filenames: Union[str, Path]) -> Optional[Commit]:
        for commit in self.iter_commits(*filenames, reverse=True):
            return commit

    def diff(self, *hash: str) -> str:
        output = subprocess.check_output(
            ["git", "diff"] + list(hash),
            cwd=self.path
        )
        return output.decode("utf-8")

    def iter_commits(
            self,
            *filenames: Union[str, Path],
            reverse: bool = False,
            offset: int = 0,
            count: int = 0,
            parse_changes: bool = True,
    ) -> Generator[Commit, None, None]:
        """
        Yields a dictionary for every git log that is found
        in the given directory.

        The ``git log`` command is used to get all the commit data.

        :param reverse: bool
            If True iterate from newest to oldest commit

        :param offset: int
            Skip these number of commits before yielding.
            (via git log --skip parameter)

        :param count: int
            If > 0 then stop after this number of commits.

        :return: generator of dict
        """
        git_cmd = [
            "git", "log",
        ]
        if parse_changes:
            git_cmd += [
                "--numstat",
                "--summary",
            ]
        git_cmd += [
            f"--pretty={self.DELIMITER1}%n"
                f"{'%n'.join(i[0] for i in self.LOG_INFOS)}"
                f"%n%B{self.DELIMITER2}",
        ] + self._git_args

        if not reverse:
            git_cmd.append("--reverse")

        if filenames:
            git_cmd += ["--"] + [str(f) for f in filenames]

        self._log(" ".join(git_cmd))
        process = subprocess.Popen(
            git_cmd,
            stdout=subprocess.PIPE,
            cwd=self.path
        )

        try:
            commit = dict()
            current_line = 0
            cur_count = 0
            while count <= 0 or (cur_count - offset) < count:
                line = process.stdout.readline()
                if not line:
                    break

                line = decode(line, ignore_errors=True).rstrip()

                # a new commit starts
                if line == self.DELIMITER1:
                    if commit:
                        if cur_count >= offset:
                            yield Commit(self, **commit)
                        cur_count += 1
                    commit = dict()
                    current_line = 0

                # commit message ended and changes (numstats) follow
                elif line == self.DELIMITER2[1:]:
                    commit["message"] = commit["message"].rstrip()
                    current_line = -1

                # digest each line
                else:
                    if 1 <= current_line <= len(self.LOG_INFOS):
                        log_info: Tuple = self.LOG_INFOS[current_line - 1]
                        value = line
                        if len(log_info) > 2:
                            value = log_info[2](value)
                        commit[log_info[1]] = value

                    elif current_line == len(self.LOG_INFOS) + 1:
                        commit["message"] = line.rstrip()
                    elif current_line > len(self.LOG_INFOS) + 1:
                        commit["message"] += "\n" + line.rstrip()

                    elif current_line == -1:
                        line = line.strip()
                        if not self._parse_changes(commit, line):
                            self._parse_summary(commit, line)

                if current_line >= 0:
                    current_line += 1

            if commit:
                if cur_count >= offset and (count <= 0 or (cur_count - offset) < count):
                    yield Commit(self, **commit)

        finally:
            process.kill()
            process.wait()

    def iter_commits_consecutive(
            self,
            offset: int = 0,
            count: int = 0,
            branch_length: int = 100,
            branch_age: int = 100,
    ) -> Generator[Commit, None, None]:

        branches = []
        for commit in self.iter_commits(offset=offset, count=count):
            if not commit.parent_hash:
                branches.append([0, commit])

            else:
                added = False
                new_branches = []
                for branch in branches:
                    for parent_hash in commit.parent_hash:
                        if not added and parent_hash == branch[-1].hash:
                            branch.append(commit)
                            added = True
                            break

                    branch[0] += 1
                    if len(branch) - 1 > branch_length or branch[0] > branch_age:
                        yield from branch[1:]
                    else:
                        new_branches.append(branch)

                branches = new_branches

                if not added:
                    branches.append([0, commit])

        for branch in branches:
            yield from branch[1:]

    def iter_commit_hashes(
            self,
            *filenames: str,
            offset: int = 0,
            count: int = 0,
            topo_order: bool = False,
            all: bool = False,
    ) -> Generator[dict, None, None]:
        """
        Yield commit hashes of the repository

        :param offset: int
            Skip these number of commits before yielding.

        :param count: int
            If > 0 then stop after this number of commits.

        :return: generator of dict
            {
                "date": datetime,
                "hash": str,
                "tree_hash": str,
                "children_hash": [str],
                "parent_hash": [str],
            }
        """
        git_cmd = [
            "git", "rev-list",
            "--children",
            "--reverse",
            "--pretty=%aI %T %P"
        ]
        if topo_order:
            git_cmd += ["--topo-order"]
        if all:
            if "--all" not in self._git_args:
                git_cmd.append("--all")
        else:
            if "--branches" not in self._git_args:
                git_cmd.append("--branches")

        if filenames:
            git_cmd += ["--"] + list(filenames)

        self._log(" ".join(git_cmd))
        process = subprocess.Popen(
            git_cmd,
            stdout=subprocess.PIPE,
            cwd=self.path
        )

        try:
            commit = dict()
            cur_count = 0
            while count <= 0 or (cur_count - offset) < count:
                line = process.stdout.readline()
                if not line:
                    break

                line = decode(line, ignore_errors=False).split()

                if line[0] == "commit":
                    commit["hash"] = line[1]
                    commit["children_hash"] = line[2:]
                else:
                    commit["date"] = parse_datetime(line[0])
                    commit["tree_hash"] = line[1]
                    commit["parent_hash"] = line[2:]
                    yield commit
                    cur_count += 1
                    commit = dict()

        finally:
            process.kill()
            process.wait()

    def iter_files(
            self,
            treeish: str,
            filenames: Optional[Sequence[str]] = None
    ) -> Generator[Tuple[BytesIO, tarfile.TarInfo], None, None]:
        """
        Iterates through all files at a commit or tree,
        by reading the tar output of `git archive`.

        :param treeish: str
        :param filenames: optional list of paths or filenames
        :return: generator of File
        """
        git_cmd = [
            "git", "archive", "--format=tar", treeish,
        ]
        if filenames:
            git_cmd += list(filenames)

        self._log(" ".join(git_cmd))
        process = subprocess.Popen(
            git_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=self.path
        )

        try:
            # TODO: would be nice if we could iterate through
            #   the files in the stdout stream but
            #   tarfile lib requires seekable streams
            #   so the whole tar-file has to be in memory

            tar_data = BytesIO(process.stdout.read())
            error_response = process.stderr.read()

        finally:
            process.kill()
            process.wait()

        tar_data.seek(0)

        try:
            for tarinfo in tarfile.open(fileobj=tar_data):
                if tarinfo.isfile():
                    yield File(self, tar_data, tarinfo)

        except tarfile.ReadError:
            if not filenames:
                return
            raise tarfile.ReadError(error_response.decode("utf-8"))

    def _parse_changes(self, commit: dict, line: str) -> bool:
        change_match = self.RE_CHANGE_NUMSTATS.match(line)
        if not change_match:
            return False

        if "changes" not in commit:
            commit["changes"] = []

        additions, deletions, name = change_match.groups()

        # TODO: additions/deletions should be integer converted
        #   but might be "-" in case of binary files
        commit["changes"].append({
            "name": name,
            "type": "change",
            "additions": additions,
            "deletions": deletions,
        })

        rename = get_git_renaming(name)
        if rename:
            commit["changes"][-1].update({
                "name": rename[1],
                "old_name": rename[0],
                "type": "rename"
            })

    def _parse_summary(self, commit: dict, line: str) -> bool:
        if line.startswith("rename "):
            return True

        change_match = self.RE_CHANGE_SUMMARY.match(line.strip())
        if not change_match:
            return False

        type, mode, name = change_match.groups()

        #if commit.get("changes"):
        for ch in commit["changes"]:
            if ch["name"] == name:
                ch["type"] = type
                ch["mode"] = mode
                return True

        #if not commit.get("changes"):
        #    commit["changes"] = []
        #    commit["changes"].append
        #print(commit)
        #print(type, mode, name)

        raise AssertionError(
            f"Expected '{name}' in --netstat changes, but got only --summary '{line}'\ncommit: {commit}"
        )
