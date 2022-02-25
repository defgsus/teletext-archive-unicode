import json
from pathlib import Path
from typing import Hashable, Dict, Tuple, Iterable, Union, Optional, Callable, List

from .calcdict import CalcDict


class TokenCounter:

    def __init__(
            self,
            tokens: Optional[Dict[Hashable, int]] = None,
            num_all: int = 0,
    ):
        self.tokens: CalcDict = CalcDict(tokens or dict())
        self.num_all = num_all

    def sorted_keys(self, key: Optional[Callable] = None, reverse: bool = True) -> List[Hashable]:
        return list(self.tokens.sorted(key=key, reverse=reverse))

    def sort(self, key: Optional[Callable] = None, reverse: bool = True):
        self.tokens = self.tokens.sorted(key=key, reverse=reverse)

    def freq_of(self, token: Hashable) -> float:
        return 0. if not self.num_all else self.tokens.get(token, 0.) / self.num_all

    def to_freq(self) -> CalcDict:
        return self.tokens / self.num_all

    def to_lowercase(self) -> "TokenCounter":
        return self.map_key(lambda k: k.lower())

    def map_key(self, func: Callable) -> "TokenCounter":
        tc = TokenCounter(num_all=self.num_all)
        for key, value in self.tokens.items():
            key = func(key)
            tc.tokens[key] = tc.tokens.get(key, 0) + value
        return tc

    def to_json(self, filename: Union[str, Path]):
        Path(filename).write_text(json.dumps(
            {
                "num_all": self.num_all,
                "tokens": self.tokens,
            },
            ensure_ascii=False,
            separators=(",", ":"),
        ))

    @classmethod
    def from_json(cls, filename: Union[str, Path]) -> "TokenCounter":
        data = json.loads(Path(filename).read_text())
        return TokenCounter(**data)

    def add(
            self,
            *token: Hashable,
            count: int = 1,
            count_all: int = 1,
    ):
        for tok in token:
            self.tokens[tok] = self.tokens.get(tok, 0) + count
        self.num_all += count_all * len(token)

    def idf(self) -> CalcDict:
        return self.tokens.inverse(self.num_all)

    def dump(self, count: int = 50, sort_key: Optional[Callable] = None, file=None):
        for key in self.sorted_keys(key=sort_key)[:count]:
            print(f"{key:30} {self.tokens[key]:9,} ({self.freq_of(key):.5f})", file=file)

