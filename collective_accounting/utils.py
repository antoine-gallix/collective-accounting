import pathlib
import sys
from decimal import Decimal

import funcy
from rich.table import Table
from rich.text import Text

import collective_accounting
from collective_accounting import logger

# ------------------------ decimal ------------------------


def round_to_cent(amount):
    return Decimal(amount).quantize(Decimal("0.01"))


def divide(amount: Decimal, denominator: Decimal) -> (Decimal, Decimal):
    quantized_result = round_to_cent(amount / denominator)
    remainder = amount - quantized_result * denominator
    return (quantized_result, remainder)


# ------------------------ ledger file ------------------------


@funcy.ignore(FileNotFoundError)
def timestamp(path):
    return pathlib.Path(path).stat().st_mtime


# ------------------------ display ------------------------


def format_balance(credit):
    formated = Text(f"{credit:+.2f}")
    if credit > 0:
        formated.style = "green"
    elif credit < 0:
        formated.style = "red"
    return formated


def build_ledger_table():
    try:
        ledger = collective_accounting.Ledger.load_from_file()
    except FileNotFoundError:
        return Text("no ledger file", style="red")
    table = Table(title="Ledger")
    table.add_column("Account")
    table.add_column("Balance")
    for account in ledger.accounts:
        table.add_row(account.name, format_balance(account.balance))
    return table
