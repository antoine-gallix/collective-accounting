import pathlib
from decimal import Decimal

import funcy
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from collective_accounting.models import Ledger

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


def build_ledger_view():
    try:
        ledger = Ledger.load_from_file()
    except FileNotFoundError:
        return Text("no ledger file", style="red")

    table = Table()
    table.add_column("Account")
    table.add_column("Balance")
    for account in ledger.accounts:
        table.add_row(account.name, format_balance(account.balance))

    header = Text(
        "\n".join(
            [
                f"file: {Ledger.LEDGER_FILE}",
                f"last update: {timestamp(Ledger.LEDGER_FILE)}",
            ]
        ),
        justify="center",
    )
    layout = Layout()
    layout.split_column(Layout(Panel(header)), Layout(Panel(table), ratio=5))
    return layout
