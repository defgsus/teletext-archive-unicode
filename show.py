import re
import json
import argparse
import datetime
import traceback
from pathlib import Path
from typing import List, Union, Tuple, Optional


from src.scraper import Scraper, scraper_classes
from src.console import ConsoleColors
from src.teletext.unico import RE_ANSI_ESCAPE
from src.teletext import Teletext, TeletextPage
from src.iterator import TeletextIterator
import src.sources


def parse_args() -> dict:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "scraper", type=str, nargs="?", default=sorted(scraper_classes)[0],
        help="scraper name"
    )
    parser.add_argument(
        "page", type=int, nargs="?", default=100,
        help="page index"
    )
    parser.add_argument(
        "sub_page", type=int, nargs="?", default=1,
        help="subpage index"
    )

    return vars(parser.parse_args())


class Viewer:

    RE_PAGE = re.compile(r"\d\d\d")
    RE_PAGE_SUB = re.compile(r"\d\d\d-\d\d?")
    RE_DAY = re.compile(r"\d\d")
    RE_MONTH_DAY = re.compile(r"\d\d-\d\d")
    RE_YEAR_MONTH_DAY = re.compile(r"\d\d\d\d-\d\d-\d\d")
    RE_YEAR = re.compile(r"\d\d\d\d")
    RE_SEARCH_RESULT = re.compile(r"\d+.")

    def __init__(
            self,
            scraper: str,
            page: int = 100,
            sub_page: int = 1,
    ):
        self.scraper: Scraper = None
        self.tt: Teletext = None
        self.pages: List[Tuple[int, int]] = []
        self.page = page
        self.sub_page = sub_page
        self.index_stack = []
        self.mode = "ansi"
        self.colors = True
        self.tt_iterator = TeletextIterator()
        self.commit_hashes = [
            json.loads(line) for line in
            (TeletextIterator.PROJECT_ROOT / "docs" / "snapshots" / "_timestamps.ndjson")
            .read_text().splitlines()
        ]
        self.commit_index = None
        self.set_scraper(scraper)
        self.search_results = []
        self.search_index = None
        self.search_query = None

    def command(self, cmd: str) -> Optional[str]:
        # print(repr(cmd))
        if self.RE_PAGE.fullmatch(cmd):
            self.set_page(int(cmd))
        elif self.RE_PAGE_SUB.fullmatch(cmd):
            index = [int(i) for i in cmd.split("-")]
            self.set_page(*index)
        elif self.RE_YEAR_MONTH_DAY.fullmatch(cmd):
            date = [int(i.lstrip("0")) for i in cmd.split("-")]
            self.set_date(*date)
        elif self.RE_MONTH_DAY.fullmatch(cmd):
            date = [int(i.lstrip("0")) for i in cmd.split("-")]
            self.set_date(None, *date)
        elif self.RE_DAY.fullmatch(cmd):
            self.set_date(None, None, int(cmd.lstrip("0")))
        elif self.RE_YEAR.fullmatch(cmd):
            self.set_date(int(cmd.lstrip("0")), 1, None)

        elif cmd == "m":
            self.mode = "ansi" if self.mode == "json" else "json"
        elif cmd == "c":
            self.colors = not self.colors
        elif cmd == "\x1b[c":  # right
            self.set_page(*self.tt.get_next_page(self.page, self.sub_page, 1))
        elif cmd == "\x1b[d":  # left
            self.set_page(*self.tt.get_next_page(self.page, self.sub_page, -1))
        elif cmd == "\x1b[a":  # up
            self.set_page(*self.tt.get_next_page(self.page, 1000, 1))
        elif cmd == "\x1b[b":  # down
            self.set_page(*self.tt.get_next_page(self.page, 0, -1))
        elif cmd == "\x1b[5~":  # page up
            self.set_page(self.page + 10, 1)
        elif cmd == "\x1b[6~":  # page down
            self.set_page(self.page - 10, 1)
        elif cmd in ("b", "back"):
            if self.index_stack:
                index = self.index_stack.pop(-1)
                self.set_page(*index, store_history=False)
        elif cmd == "+":
            if self.commit_index is not None:
                self.commit_index += 1
                if self.commit_index >= len(self.commit_hashes):
                    self.commit_index = None
                self.set_scraper(self.scraper.NAME)
        elif cmd == "-":
            if self.commit_index is None:
                self.commit_index = len(self.commit_hashes) - 1
            else:
                if self.commit_index > 0:
                    self.commit_index -= 1
                    self.set_scraper(self.scraper.NAME)

        elif cmd.startswith("s "):
            query = cmd[2:].strip()
            self.search(query)
        elif self.RE_SEARCH_RESULT.fullmatch(cmd):
            self.set_search_index(max(0, min(len(self.search_results) - 1, int(cmd[:-1]) - 1)))

        elif cmd in scraper_classes:
            self.set_scraper(cmd)
        else:
            return f"Unknown command {repr(cmd)}"

    def render(self):
        header = f"page {self.page}-{self.sub_page} ({self.tt.timestamp.replace('T', ' ')})" \
            + f" ({self.scraper.get_page_category(self.page, self.tt.timestamp)})"
        index = (self.page, self.sub_page)

        panel_str = (
            self.history_str() + "\n" +
            self.help_str()
        )
        search_str = self.search_str()

        if index not in self.tt.pages:
            page_text = f"{header} not found\n"
        else:
            page = self.tt.pages[index]

            page_text = f"{header}\n"
            if self.mode == "ansi":
                page_text += page.to_ansi(colors=self.colors, border=True)
                # Path("ansi.txt").write_text(tt.to_ansi(colors=self.colors))
            else:
                page_text = page.to_ndjson()

        print(self.side_by_side(page_text, panel_str, search_str))

    def history_str(self) -> str:
        if self.commit_index is None:
            top_index = len(self.commit_hashes) - 1
        else:
            top_index = min(len(self.commit_hashes) - 1, max(9, self.commit_index + 5))
        return "\n".join(
            ("*" if self.commit_index == top_index - i else " ")
            + " " + self.commit_hashes[top_index - i]['timestamp'].replace("T", " ")
            for i in range(10)
        ) + "\n"

    def search_str(self) -> str:
        if not self.search_results:
            return ""
        if self.search_index is None:
            top_index = 0
        else:
            top_index = max(0, min(len(self.search_results) - 25, self.search_index - 12))
        lines = []
        for i in range(min(25, len(self.search_results))):
            idx = top_index + i
            c = self.search_results[idx]
            line = "*" if self.search_index == idx else " "
            line += f"{idx + 1:3}. " + c['timestamp'][:10] + " " + c["channel"] + " %s-%s" % c["page"]
            lines.append(line)
        return f"{len(self.search_results)} results for '{self.search_query}':\n\n" + "\n".join(lines)

    def help_str(self) -> str:
        help = (
            "q = quit, m = mode, c = color\n"
            "page: 0-9, up/down, right/left,\n"
            "  b = back\n"
            "history: -/+, [[YYYY-]MM]-DD\n"
            "channels: " + ", ".join(sorted(scraper_classes)[:5]) + "\n"
            "  " + ", ".join(sorted(scraper_classes)[5:]) + "\n"
        )
        return help

    @classmethod
    def side_by_side(cls, text1: str, *text2: str, distance: int = 2) -> str:
        if not text2:
            return text1
        elif len(text2) > 1:
            return cls.side_by_side(
                cls.side_by_side(text1, text2[0], distance=distance),
                *text2[1:],
                distance=distance,
            )
        lines1 = text1.splitlines()
        lines2 = text2[0].splitlines()
        lines1_no_ansi = RE_ANSI_ESCAPE.sub("", text1).splitlines()
        line1_width = max(0, 0, *(len(l) for l in lines1_no_ansi))
        ret_lines = []
        for i in range(max(len(lines1), len(lines2))):
            if i >= len(lines1):
                line1 = " " * line1_width
            else:
                line1 = lines1[i] + " " * (line1_width - len(lines1_no_ansi[i]))
            ret_lines.append(
                line1 + " " * distance + (
                    lines2[i] if i < len(lines2) else ""
                )
            )
        return "\n".join(ret_lines)

    def set_scraper(self, scraper: str):
        self.scraper: Scraper = scraper_classes[scraper]()
        if self.commit_index is None:
            self.tt = Teletext.from_ndjson(self.scraper.filename())
        else:
            self.tt = self.tt_iterator.get_historic_teletext(
                scraper, self.commit_hashes[self.commit_index]["hash"]
            )
            if not self.tt:
                self.tt = Teletext()
                self.tt.timestamp = self.commit_hashes[self.commit_index]["timestamp"]
                self.tt.commit_hash = self.commit_hashes[self.commit_index]["hash"]
                page = TeletextPage()
                page.new_line()
                page.add_block(TeletextPage.Block(f"{scraper} @ {self.tt.timestamp} not found"))
                self.tt.pages[(100, 1)] = page
                self.tt.page_index = [(100, 1)]

        self.set_page(self.page, self.sub_page)

    def set_page(self, page: int, sub_page: int = 1, store_history: bool = True):
        if store_history:
            index = (self.page, self.sub_page)
            if not self.index_stack or self.index_stack[-1] != index:
                self.index_stack.append(index)

        self.page, self.sub_page = self.tt.get_next_page(page, sub_page, 0)

    def set_date(self, year: Optional[int], month: Optional[int] = None, day: Optional[int] = None):
        today = datetime.date.today()
        if year is None:
            year = today.year
        if month is None:
            month = today.month
        if day is None:
            day = 1

        commit_index = 0
        date_str = f"{year:04}-{month:02}-{day:02}"
        for i, commit in enumerate(self.commit_hashes):
            commit_date_str = commit["timestamp"][:10]
            if date_str <= commit_date_str:
                commit_index = i
                break
        self.commit_index = commit_index
        self.set_scraper(self.scraper.NAME)

    def set_commit_hash(self, hash: str, update_scraper: bool = True):
        commit_index = None
        for i, commit in enumerate(self.commit_hashes):
            if commit["hash"].startswith(hash):
                commit_index = i
                break
        self.commit_index = commit_index
        self.set_scraper(self.scraper.NAME)

    def search(self, query: str):
        from elastipy import Search

        date = None
        if query and query[0].isnumeric():
            query = query.split()
            date_str = query[0]
            query = " ".join(query[1:])
            for date_fmt in ("%Y-%m-%d", "%m-%d"):
                try:
                    date = datetime.datetime.strptime(date_str, date_fmt).date()
                    if date.year < 2022:
                        date = date.replace(year=2022)
                    break
                except ValueError:
                    pass
            if not date:
                print(f"Invalid date '{date_str}' in search")
                return

        s = (
            Search("teletext-archive")
            .match("text", query, operator="and")
        )
        if date:
            s = s.range("timestamp", gte=date, lte=date)
        result = (
            s.size(1000)
            .sort("-timestamp")
            .execute()
        )
        self.search_results = [
            {
                "timestamp": doc["timestamp"],
                "hash": doc["commit_hash"],
                "channel": doc["channel"],
                "page": (doc["main_page"], doc["sub_page"]),
            }
            for doc in result.documents
        ]
        self.search_query = query
        self.set_search_index(0)

    def set_search_index(self, index: int):
        if not self.search_results:
            self.search_index = None
        else:
            self.search_index = max(0, min(len(self.search_results) - 1, index))

            r = self.search_results[self.search_index]
            if r["channel"] != self.scraper.NAME:
                self.set_commit_hash(r["hash"], update_scraper=False)
                self.set_scraper(r["channel"])
            else:
                self.set_commit_hash(r["hash"])
            self.set_page(*r["page"])


def main(
        scraper: str,
        page: int,
        sub_page: int
):
    print(ConsoleColors.CLEAR, end="")
    viewer = Viewer(scraper, page, sub_page)
    viewer.render()

    try:
        while True:

            cmd = input("> ").lower()

            if cmd == "q":
                break

            print(ConsoleColors.CLEAR, end="")
            if cmd:
                msg = viewer.command(cmd)
                if msg:
                    print(msg)

            viewer.render()

    except (KeyboardInterrupt, EOFError):
        print()


if __name__ == "__main__":
    main(**parse_args())
