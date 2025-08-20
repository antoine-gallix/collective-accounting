import pathlib
from decimal import Decimal

import funcy

# ------------------------ decimal ------------------------


def round_to_cent(amount):
    return Decimal(amount).quantize(Decimal("0.01"))


def divide(amount: Decimal, denominator: Decimal) -> (Decimal, Decimal):
    quantized_result = round_to_cent(amount / denominator)
    remainder = amount - quantized_result * denominator
    return (quantized_result, remainder)


# ------------------------ ledger file ------------------------


@funcy.ignore(FileNotFoundError)
def file_modification_timestamp(path):
    return pathlib.Path(path).stat().st_mtime


@funcy.ignore(FileNotFoundError)
def file_creation_timestamp(path):
    return pathlib.Path(path).stat().st_atime
