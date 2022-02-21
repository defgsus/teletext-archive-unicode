"""
Script for converting the original defgsus/teletext-archive commits
to new format and commit in new repository
"""
import os
import json
from pathlib import Path
from typing import List, Dict, Tuple, Callable, Any

import pytz
from tqdm import tqdm

from src.scraper import Scraper, scraper_classes
import src.sources
from src.giterator import Giterator


def main():
    git = Giterator(
        Path(__file__).resolve().parent.parent.parent / "teletext-archive"
    )

    for commit in tqdm(git.iter_commits("docs/snapshots"), desc="commits", total=git.num_commits()):

        timestamp = commit.author_date.astimezone(pytz.utc).replace(tzinfo=None).isoformat()

        scraper_file_dict: Dict[str, Dict[Tuple[int, int], bytes]] = {}
        for file in commit.iter_files(["docs/snapshots"]):
            scraper_name, file_name = file.name.split("/")[-2:]
            if file_name == "status.json":
                continue

            if scraper_name not in scraper_file_dict:
                scraper_file_dict[scraper_name] = {}

            scraper_file_dict[scraper_name][
                tuple(int(i.lstrip("0")) for i in file_name.split(".", 1)[0].split("-"))
            ] = file.data

        commit_msg = f"replayed commit from {timestamp}"

        for scraper_name in sorted(scraper_file_dict):
            page_bytes = scraper_file_dict[scraper_name]
            scraper = scraper_classes[scraper_name]()

            report = render_teletext(
                scraper=scraper,
                page_bytes=page_bytes,
                timestamp=timestamp,
            )

            commit_msg += f"\n\n### {scraper.NAME}\n\n"

            for key, value in report.items():
                if value:
                    key_name = key
                    if key == "errors":
                        key_name = "had errors"
                    commit_msg += f"- {value} pages {key_name}\n"

        print(commit_msg)


def render_teletext(
        scraper: Scraper,
        page_bytes: Dict[Tuple[int, int], bytes],
        timestamp: str,
) -> dict:
    """
    Simulate a scraping session

    Returns a small report dict.
    """
    scraper.load_previous_pages()
    report = {
        "changed": 0,
        "added": 0,
        "removed": 0,
        "unchanged": 0,
        "errors": 0,
    }
    retrieved_set = set()

    os.makedirs(scraper.filename().parent, exist_ok=True)
    with open(str(scraper.filename()), "w") as fp:
        header = {
            "scraper": scraper.NAME, "timestamp": timestamp
        }
        print(json.dumps(header, ensure_ascii=False, separators=(',', ':')), file=fp)

        for (page_num, sub_page_num), binary_content in tqdm(page_bytes.items(), desc=scraper.NAME):
            retrieved_set.add((page_num, sub_page_num))

            content = scraper.legacy_bytes_to_content(binary_content)

            page = scraper.to_teletext(content)
            page.index = page_num
            page.sub_index = sub_page_num
            page.timestamp = timestamp

            previous_page = scraper.previous_pages.get_page(page_num, sub_page_num)
            if previous_page:
                # if nothing changed (according to scraper's comparison)
                #   write the previous page with it's timestamp and everything
                #   to minimize commit changes
                if scraper.compare_pages(previous_page, page):
                    page = previous_page
                    report["unchanged"] += 1
                    scraper.log(f"no change in {page_num}/{sub_page_num}")
                else:
                    report["changed"] += 1
                    scraper.log(f"{page_num}/{sub_page_num} has changed")
            else:
                report["added"] += 1
                scraper.log(f"{page_num}/{sub_page_num} is new")

            page.to_ndjson(file=fp)

    report["removed"] = len(set(scraper.previous_pages.page_index) - retrieved_set)

    return report


if __name__ == "__main__":
    main()
