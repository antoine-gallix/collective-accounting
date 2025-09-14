from decimal import Decimal
from typing import Self

import funcy

# ------------------------ decimal ------------------------

type Amount = Decimal | int


class Money(Decimal):
    CURRENCY = "€"

    def __new__(cls, number):
        return super().__new__(cls, Decimal(number).quantize(Decimal("0.01")))

    def __repr__(self):
        return f"{self.__class__.__name__}('{self}')"

    def __str__(self):
        return super().__format__("+") + self.CURRENCY

    def __format__(self, _):
        return str(self)

    def __add__(self, something):
        return self.__class__(super().__add__(something))

    def __sub__(self, something):
        return self.__class__(super().__sub__(something))

    def __neg__(self):
        return self.__class__(super().__neg__())

    def __truediv__(self, something):
        return self.__class__(super().__truediv__(something))

    def __mul__(self, something):
        return self.__class__(super().__mul__(something))

    def divide_with_no_rest(self, by: int) -> list[Self]:
        """Split a into parts as equal as possible, without error, rounded to cent"""
        quantized_result = self / by
        remainder = self - quantized_result * by
        return funcy.lmap(
            self.__class__,
            funcy.concat(
                [quantized_result + remainder],
                funcy.repeat(quantized_result, by - 1),
            ),
        )
