import os
import sys
import json
import glob
import datetime
import time
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
    REQUEST_TIMEOUT: float = 20
    REQUEST_RETRIES: int = 3

    BASE_PATH: Path = Path(__file__).resolve().parent.parent / "docs" / "snapshots"

    PAGE_CATEGORIES = {
        100: "index",
        101: "undefined",
    }

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

    def get_page_category(self, page: int, timestamp: str) -> str:
        last_category = "undefined"
        for num in sorted(self.PAGE_CATEGORIES):
            if page == num:
                return self.PAGE_CATEGORIES[num]
            if num > page:
                return last_category
            last_category = self.PAGE_CATEGORIES[num]
        return last_category

    def compare_pages(self, old: TeletextPage, new: TeletextPage) -> bool:
        """
        Override this to compare pages without, e.g. an imprinted timestamp.
        No use in committing changes like this.
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
            "changed": 0,
            "added": 0,
            "removed": 0,
            "unchanged": 0,
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
                    self.log(f"no change in {page_num}/{sub_page_num}")

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
                            self.log(f"no change in {page_num}/{sub_page_num}")
                        else:
                            report["changed"] += 1
                            self.log(f"{page_num}/{sub_page_num} has changed")
                    else:
                        report["added"] += 1
                        self.log(f"{page_num}/{sub_page_num} is new")

                page.to_ndjson(file=fp)

        report["removed"] = len(set(self.previous_pages.page_index) - retrieved_set)

        return report

    def log(self, *args):
        if self.verbose:
            print(f"{self.__class__.__name__}:", *args, file=sys.stderr)

    def get_html(self, url: str, method: str = "GET", **kwargs) -> requests.Response:
        kwargs.setdefault("timeout", self.REQUEST_TIMEOUT)
        self.log("requesting", url)

        for i in range(self.REQUEST_RETRIES):
            try:
                return self.session.request(method=method, url=url, **kwargs)
            except requests.RequestException:
                if i + 1 < self.REQUEST_RETRIES:
                    raise
                time.sleep(3)

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

    @classmethod
    def legacy_bytes_to_content(cls, content: bytes) -> Any:
        return content.decode("utf-8")
