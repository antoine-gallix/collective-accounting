import arrow
from rich.align import Align
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .models import Ledger
from .utils import file_creation_timestamp, file_modification_timestamp


def format_balance(credit):
    formated = Text(f"{credit:+.2f}")
    if credit > 0:
        formated.style = "green"
    elif credit < 0:
        formated.style = "red"
    return formated


def format_timestamp(timestamp):
    return arrow.get(timestamp).to("local").format("YYYY-MM-DD HH:mm:ss")


def make_file_view(ledger):
    elements = [
        f"file: {Ledger.LEDGER_FILE}",
        f"creation: {format_timestamp(file_creation_timestamp(Ledger.LEDGER_FILE))}",
        f"last update: {format_timestamp(file_modification_timestamp(Ledger.LEDGER_FILE))}",
    ]
    view = Layout()
    view.split_row(*[Layout(Text(element, justify="center")) for element in elements])
    return view


def make_ledger_view(ledger):
    table = Table()
    table.add_column("Account")
    table.add_column("Balance")
    for account in ledger.accounts:
        table.add_row(account.name, format_balance(account.balance))
    return table


def build_ledger_view():
    try:
        ledger = Ledger.load_from_file()
    except FileNotFoundError:
        return Text("no ledger file", style="red")

    file_view = make_file_view(ledger)
    ledger_view = make_ledger_view(ledger)
    layout = Layout()
    layout.split_column(
        Layout(Panel(file_view, title="file"), size=3),
        Layout(
            Panel(Align(ledger_view, align="center", vertical="middle"), title="ledger")
        ),
    )

    return layout
