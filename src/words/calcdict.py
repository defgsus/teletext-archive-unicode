import math
from typing import Union, Optional, Callable


Number = Union[int, float]


class CalcDict(dict):
    
    def __copy__(self):
        return CalcDict(self)

    def __iadd__(self, other: dict) -> "CalcDict":
        for key, value in other.items():
            self[key] = self.get(key, 0) + value
        return self

    def __add__(self, other: dict) -> "CalcDict":
        new_dict = self.__copy__()
        new_dict += other
        return new_dict
    
    def __isub__(self, other: dict) -> "CalcDict":
        for key, value in other.items():
            self[key] = self.get(key, 0) - value
        return self

    def __sub__(self, other: "CalcDict") -> "CalcDict":
        new_dict = self.__copy__()
        new_dict -= other
        return new_dict

    def __imul__(self, value: Union[Number, dict]) -> "CalcDict":
        if isinstance(value, dict):
            for key, v in value.items():
                if key in self:
                    self[key] *= v
        else:
            for key in self:
                self[key] *= value
        return self

    def __mul__(self, other: Union[Number, dict]) -> "CalcDict":
        new_dict = self.__copy__()
        new_dict *= other
        return new_dict

    def __itruediv__(self, value: Number) -> "CalcDict":
        for key in self:
            self[key] /= value
        return self

    def __truediv__(self, other: Number) -> "CalcDict":
        new_dict = self.__copy__()
        new_dict /= other
        return new_dict

    def sorted(self, key: Optional[Callable] = None, reverse: bool = False) -> "CalcDict":
        return CalcDict({
            key: self[key]
            for key in sorted(
                sorted(self, reverse=reverse),
                key=key or self._default_sort_key,
                reverse=reverse
            )
        })

    def limited(self, min_value: Optional[int] = None, max_value: Optional[int] = None) -> "CalcDict":
        new_dict = CalcDict()
        for key, value in self.items():
            if min_value is None or value >= min_value:
                if max_value is None or value <= max_value:
                    new_dict[key] = value
        return new_dict

    def inverse(self, n: int) -> "CalcDict":
        return CalcDict({
            key: math.log(n / value) if value else 0
            for key, value in self.items()
        })

    def _default_sort_key(self, key):
        return self[key]

    def dump(self, limit: int = 50, sort_key: Optional[Callable] = None, reverse: bool = False, file=None):
        for key in sorted(
                sorted(self, reverse=reverse),
                key=sort_key or self._default_sort_key, reverse=reverse
        )[:limit]:
            print(f"{key:30} {self[key]:.5f}", file=file)
