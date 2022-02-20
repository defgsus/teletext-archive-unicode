import sys
import argparse
import datetime
import traceback
from pathlib import Path
from typing import List, Union, Tuple, Optional


from src.scraper import Scraper, scraper_classes
from src.console import ConsoleColors
from src.teletext import Teletext
import src.sources


def parse_args() -> dict:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "scraper", type=str,
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
        self.mode = "ansi"
        self.colors = True
        self.set_scraper(scraper)

    def command(self, cmd: str) -> Optional[str]:
        # print(repr(cmd))
        try:
            new_page = int(cmd)
            self.set_page(new_page)
            return
        except ValueError:
            pass

        if cmd == "m":
            self.mode = "ansi" if self.mode == "json" else "json"
        elif cmd == "c":
            self.colors = not self.colors
        elif cmd == "\x1b[c":
            self.set_page(*self.tt.get_next_page(self.page, self.sub_page, 1))
        elif cmd == "\x1b[d":
            self.set_page(*self.tt.get_next_page(self.page, self.sub_page, -1))
        elif cmd == "\x1b[a":  # end
            self.set_page(*self.tt.get_next_page(self.page, 1000, 1))
        elif cmd == "\x1b[b":  # pos1
            self.set_page(*self.tt.get_next_page(self.page, 0, -1))
        elif cmd == "\x1b[5~":  # page up
            self.set_page(self.page + 10, 1)
        elif cmd == "\x1b[6~":  # page down
            self.set_page(self.page - 10, 1)
        elif cmd in scraper_classes:
            self.set_scraper(cmd)
        else:
            return f"Unknown command {repr(cmd)}"

    def render(self):
        page = self.tt.pages[(self.page, self.sub_page)]

        print(f"page {self.page}-{self.sub_page}\n")
        if self.mode == "ansi":
            print(page.to_ansi(colors=self.colors))
            #Path("ansi.txt").write_text(tt.to_ansi(colors=True))
        else:
            print(page.to_ndjson())
        print(self.help_str())

    def help_str(self) -> str:
        help = "q = quit, m = mode, c = color\n"
        help += "page: 0-9, up/down, right/left\n"
        help += ", ".join(scraper_classes) + "\n"
        return help

    def set_scraper(self, scraper: str):
        self.scraper: Scraper = scraper_classes[scraper]()
        self.tt = Teletext.from_ndjson(self.scraper.filename())
        self.set_page(self.page, self.sub_page)

    def set_page(self, page: int, sub_page: int = 1):
        self.page, self.sub_page = self.tt.get_next_page(page, sub_page, 0)



def main(
        scraper: str,
        page: int,
        sub_page: int
):
    viewer = Viewer(scraper, page, sub_page)
    viewer.render()

    try:
        while True:

            cmd = input("> ").lower()

            if cmd == "q":
                break

            if cmd:
                msg = viewer.command(cmd)
                if msg:
                    print(msg)
                else:
                    viewer.render()

    except (KeyboardInterrupt, EOFError):
        print()


if __name__ == "__main__":
    main(**parse_args())
