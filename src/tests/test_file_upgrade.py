import unittest
import shutil
from pathlib import Path
from typing import Dict, Tuple, Generator, Union

from src.scraper import Scraper


class FakeScraper(Scraper):
    NAME = "TEST"

    def __init__(self, page_content: Dict[Tuple[int, int], str]):
        super().__init__()
        self._page_content = page_content

    def iter_pages(self) -> Generator[Tuple[int, int, Union[str, bool]], None, None]:
        for (page_index, sub_page_index), content in self._page_content.items():
            yield page_index, sub_page_index, content


class TestFileUpgrade(unittest.TestCase):

    def setUp(self) -> None:
        if FakeScraper.path().exists():
            shutil.rmtree(str(FakeScraper.path()))

    def tearDown(self) -> None:
        if FakeScraper.path().exists():
            shutil.rmtree(str(FakeScraper.path()))

    def assert_files(self, page_content: Dict[Tuple[int, int], str]):
        expected_files = [
            (
                f"{page_index:0{FakeScraper.NUM_PAGE_DIGITS}}"
                f"-{sub_page_index:0{FakeScraper.NUM_SUB_PAGE_DIGITS}}"
                f".{FakeScraper.FILE_EXTENSION}",
                content
            )
            for (page_index, sub_page_index), content in page_content.items()
        ]
        expected_filenames = [f[0] for f in expected_files]
        filenames = sorted(f.name for f in FakeScraper.path().glob(f"*.{FakeScraper.FILE_EXTENSION}"))
        self.assertEqual(expected_filenames, filenames)

        for fn, expected_content in expected_files:
            content = (FakeScraper.path() / fn).read_text()
            self.assertEqual(
                expected_content,
                content,
                f"In {fn}"
            )

    def test_100_upgrade(self):
        page_content = {
            (100, 1): "a",
            (101, 1): "b",
            (101, 2): "c",
        }
        report = FakeScraper(page_content).download()
        self.assert_files(page_content)
        self.assertEqual(
            {
                "changed": 0,
                "unchanged": 0,
                "added": 3,
                "removed": 0,
            },
            report,
        )

        report = FakeScraper(page_content).download()
        self.assert_files(page_content)
        self.assertEqual(
            {
                "changed": 0,
                "unchanged": 3,
                "added": 0,
                "removed": 0,
            },
            report,
        )

        page_content = {
            (100, 1): "a1",
            (101, 1): "b",
            (101, 2): "c2",
        }
        report = FakeScraper(page_content).download()
        self.assert_files(page_content)
        self.assertEqual(
            {
                "changed": 2,
                "unchanged": 1,
                "added": 0,
                "removed": 0,
            },
            report,
        )

        page_content = {
            (100, 1): "a5",
            (101, 1): "b",
        }
        report = FakeScraper(page_content).download()
        self.assert_files(page_content)
        self.assertEqual(
            {
                "changed": 1,
                "unchanged": 1,
                "added": 0,
                "removed": 1,
            },
            report,
        )

        page_content = {
            (100, 1): True,  # scraper's way of saying it hasn't changed
            (101, 1): True,
            (101, 2): "c",
            (101, 3): "d",
        }
        report = FakeScraper(page_content).download()
        self.assert_files({
            (100, 1): "a5",
            (101, 1): "b",
            (101, 2): "c",
            (101, 3): "d",
        })
        self.assertEqual(
            {
                "changed": 0,
                "unchanged": 2,
                "added": 2,
                "removed": 0,
            },
            report,
        )