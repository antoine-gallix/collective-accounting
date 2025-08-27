import pathlib
from decimal import Decimal

import funcy

# ------------------------ decimal ------------------------

type Amount = Decimal | int


def round_to_cent(amount):
    return Decimal(amount).quantize(Decimal("0.01"))


class Money(Decimal):
    CURRENCY = "€"

    def __new__(cls, number):
        return super().__new__(cls, Decimal(number).quantize(Decimal("0.01")))

    def __repr__(self):
        return f"{self.__class__.__name__}('{self}')"

    def __str__(self):
        a = super().__str__()
        return f"{a}{self.CURRENCY}"

    def __add__(self, something):
        return self.__class__(super().__add__(something))

    def divide(self, by: int) -> list[Decimal]:
        """Split a into parts as equal as possible, without error, rounded to cent"""
        quantized_result = round_to_cent(self / by)
        remainder = self - quantized_result * by
        return funcy.lmap(
            self.__class__,
            funcy.concat(
                [quantized_result + remainder],
                funcy.repeat(quantized_result, by - 1),
            ),
        )


def divide(amount: Amount, denominator: int) -> list[Decimal]:
    """Split a decimal amount into parts as equal as possible, without error, rounded to cent"""
    quantized_result = round_to_cent(amount / denominator)
    remainder = amount - quantized_result * denominator
    return funcy.lconcat(
        [quantized_result + remainder], funcy.repeat(quantized_result, denominator - 1)
    )


# ------------------------ ledger file ------------------------


@funcy.ignore(FileNotFoundError)
def file_modification_timestamp(path):
    return pathlib.Path(path).stat().st_mtime


@funcy.ignore(FileNotFoundError)
def file_creation_timestamp(path):
    return pathlib.Path(path).stat().st_atime
