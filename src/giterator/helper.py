import os
import re
import math
import datetime
from typing import Optional, Tuple, List, Any, Sequence, Iterable

import dateutil.parser


RE_MULTI_SLASH = re.compile(r"/+")

_date_parser = dateutil.parser


def parse_datetime(s: str) -> datetime.datetime:
    return _date_parser.parse(s)


def decode(s: bytes, ignore_errors: bool = False) -> Optional[str]:
    for encoding in ("latin1", "utf-8"):
        try:
            return s.decode(encoding)
        except UnicodeDecodeError:
            pass
    if ignore_errors:
        return s.decode("utf-8", errors="ignore")
    else:
        return None


def safe_console_string(msg: str) -> str:
    # these characters block the console output
    return msg.replace("\x90", r"\x90").replace("\x98", r"\x98")


def get_git_renaming(name: str) -> Optional[Tuple[str, str]]:
    if " => " not in name:
        return

    try:
        idx_start = name.index("{")
        idx_end = name.index("}")
    except ValueError:
        name1, name2 = name.split(" => ")
        return name1, name2

    middle = name[idx_start+1:idx_end].split(" => ")
    name1 = name[:idx_start] + middle[0] + name[idx_end+1:]
    name2 = name[:idx_start] + middle[1] + name[idx_end+1:]
    return RE_MULTI_SLASH.sub("/", name1), RE_MULTI_SLASH.sub("/", name2)


MEM_SCALE = {
    "kb": 1024,
    "mb": 1024 * 1024,
    "gb": 1024 * 1024 * 1024,
}


def get_memory_usage() -> int:
    """
    Returns the current memory usage of the process in bytes,
    or ``0`` if not available/working
    :return: int
    """
    try:
        with open(f"/proc/{os.getpid()}/status") as f:
            status = f.read()
    except:
        return 0

    try:
        mem_str = status[status.index("VmSize:")+7:].splitlines()[0].split()
        return int(mem_str[0]) * MEM_SCALE[mem_str[1].lower()]
    except (IndexError, KeyError):
        return 0
