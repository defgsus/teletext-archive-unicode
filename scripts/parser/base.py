from typing import List, Union, Tuple, Iterable

from src.teletext import Teletext, TeletextPage


class TeletextParserBase:

    channels: List[str] = None

    registered_classes = {}

    GERMAN_MONTH_NAMES = [
        "Januar", "Februar", "März", "April", "Mai", "Juni", "Juli",
        "August", "September", "Oktober", "November", "Dezember",
    ]

    def __init_subclass__(cls, **kwargs):
        if cls.__name__ in TeletextParserBase.registered_classes:
            raise ValueError(f"Name '{cls.__name__}' already taken")
        #if not cls.SOURCE:
        #    raise ValueError(f"Must define {cls.__name__}.SOURCE")
        TeletextParserBase.registered_classes[cls.__name__] = cls

    def __init__(self, bucket_receiver):
        self._bucket_receiver = bucket_receiver

    def add_bucket(self, timestamp: str, key: Union[str, Tuple[str, ...]], value):
        self._bucket_receiver.add_bucket(timestamp, key, value)

    def parse_buckets(self, tt: Teletext):
        for name in filter(lambda n: n.startswith("parse_buckets_"), dir(self)):
            func = getattr(self, name)
            if callable(func):
                page_numbers = [int(n.lstrip("0") or 0) for n in name[14:].split("_")]
                if len(page_numbers) > 1:
                    page_numbers = list(range(page_numbers[0], page_numbers[1]))

                for page_number in page_numbers:

                    sub_page = 0
                    while True:
                        sub_page += 1
                        page = tt.get_page(page_number, sub_page)
                        if not page:
                            if sub_page == 1:
                                print(f"{self.__class__.__name__}: page {page_number} missing")
                            break

                        func(page)

    def page_to_lines(self, page: TeletextPage) -> List[str]:
        return page.to_ansi(colors=False).replace("\xa0", " ").splitlines()

    def split_lines_vertical(self, lines: Iterable[str], *split_points: int):
        for line in lines:
            split_line = []

            prev_x = None
            for x in split_points:
                split_line.append(line[prev_x:x])
                prev_x = x

            split_line.append(line[prev_x:])

            yield split_line
