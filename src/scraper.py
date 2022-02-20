import os
import sys
import json
import glob
import datetime
from pathlib import Path
from typing import Generator, Tuple, Union, Optional, Any

import requests
import bs4

from .teletext import Teletext, TeletextPage

scraper_classes = dict()


class Scraper:

    # must be filename compatible
    NAME: str = None
    # set to True in abstract classes
    ABSTRACT: bool = False

    # request timeout in seconds
    REQUEST_TIMEOUT: float = 10

    BASE_PATH: Path = Path(__file__).resolve().parent.parent / "docs" / "snapshots"

    def __init_subclass__(cls, **kwargs):
        if not cls.ABSTRACT:
            assert cls.NAME, f"Define {cls.__name__}.NAME"

            if cls.NAME in scraper_classes:
                raise AssertionError(f"Duplicate name '{cls.NAME}' for class {cls.__name__}")

            scraper_classes[cls.NAME] = cls

    def __init__(self, verbose: bool = False, raise_errors: bool = False):
        self.verbose = verbose
        self.do_raise_errors = raise_errors
        self.previous_pages = Teletext()
        self.session = requests.Session()
        self.session.headers = {
            "User-Agent": "github.com/defgsus/teletext-archive-unicode"
        }

    @classmethod
    def path(cls) -> Path:
        return cls.BASE_PATH

    @classmethod
    def filename(cls) -> Path:
        return cls.path() / f"{cls.NAME}.ndjson"

    def iter_pages(self) -> Generator[Tuple[int, int, Any], None, None]:
        """
        Yield tuples of (page-number, sub-page-number, content)

        Page-number starts at 100, sub-page number starts at 1

        Content should be the thing that is handled by .to_teletext()

        One special case is content == True, in which case the previous page
        will be reused. You should be sure, however, that the
        page-number/sub-page-number is in fact in self.previous_pages!
        """
        raise NotImplementedError

    def to_teletext(self, content: Any) -> Optional[TeletextPage]:
        raise NotImplementedError

    def compare_pages(self, old: TeletextPage, new: TeletextPage) -> bool:
        """
        Override this to compare pages without, e.g. an imprinted timestamp.
        New use in committing changes like this.
        """
        return old == new

    def load_previous_pages(self):
        self.previous_pages = Teletext()
        if self.filename().exists():
            try:
                self.previous_pages = Teletext.from_ndjson(self.filename())
            except Exception as e:
                self.log(f"{type(e).__class__}: {e}")
                pass

    def download(self) -> dict:
        """
        Download all pages via `iter_pages` and store to disk

        Returns a small report dict.
        """
        self.load_previous_pages()
        report = {
            "unchanged": 0,
            "changed": 0,
            "added": 0,
            "removed": 0,
            "errors": 0,
        }
        retrieved_set = set()

        self.log("writing", self.filename())
        os.makedirs(self.filename().parent, exist_ok=True)
        with open(str(self.filename()), "w") as fp:
            header = {
                "scraper": self.NAME, "timestamp": datetime.datetime.utcnow().replace(microsecond=0).isoformat()
            }
            print(json.dumps(header, ensure_ascii=False, separators=(',', ':')), file=fp)

            for page_num, sub_page_num, content in self.iter_pages():
                retrieved_set.add((page_num, sub_page_num))

                if content is True:
                    page = self.previous_pages.get_page(page_num, sub_page_num)
                    report["unchanged"] += 1

                else:
                    timestamp = datetime.datetime.utcnow().replace(microsecond=0).isoformat()

                    try:
                        page = self.to_teletext(content)
                    except Exception as e:
                        if self.do_raise_errors:
                            raise
                        self.log(f"CONVERSION ERROR: {type(e).__name__}: {e}")
                        page = TeletextPage()
                        page.error = f"{type(e).__name__}: {e}"
                        report["errors"] += 1

                    page.index = page_num
                    page.sub_index = sub_page_num
                    page.timestamp = timestamp

                    previous_page = self.previous_pages.get_page(page_num, sub_page_num)
                    if previous_page:
                        # if nothing changed (according to scraper's comparison)
                        #   write the previous page with it's timestamp and everything
                        #   to minimize commit changes
                        if self.compare_pages(previous_page, page):
                            page = previous_page
                            report["unchanged"] += 1
                        else:
                            report["changed"] += 1
                    else:
                        report["added"] += 1

                page.to_ndjson(file=fp)

        report["removed"] = len(set(self.previous_pages.page_index) - retrieved_set)

        return report

    def log(self, *args):
        if self.verbose:
            print(f"{self.__class__.__name__}:", *args, file=sys.stderr)

    def get_html(self, url: str, method: str = "GET", **kwargs) -> requests.Response:
        kwargs.setdefault("timeout", self.REQUEST_TIMEOUT)
        self.log("requesting", url)
        return self.session.request(method=method, url=url, **kwargs)

    def get_soup(
            self,
            url: str,
            method: str = "GET",
            expected_status: int = 200,
            **kwargs
    ) -> Optional[bs4.BeautifulSoup]:
        response = self.get_html(url=url, method=method, **kwargs)
        if response.status_code != expected_status:
            return None
        return self.to_soup(response.text)

    @classmethod
    def to_soup(cls, markup: str) -> bs4.BeautifulSoup:
        return bs4.BeautifulSoup(markup, features="html.parser")
