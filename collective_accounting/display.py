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


def make_file_info_view(ledger):
    table = Table.grid(padding=(0, 5))
    table.add_row("file", str(Ledger.LEDGER_FILE))
    table.add_row(
        "creation", format_timestamp(file_creation_timestamp(Ledger.LEDGER_FILE))
    )
    table.add_row(
        "last update",
        format_timestamp(file_modification_timestamp(Ledger.LEDGER_FILE)),
    )
    return table


def make_balance_view(ledger):
    table = Table()
    for account in ledger.accounts:
        table.add_column(account.name)
    table.add_row(*(format_balance(account.balance) for account in ledger.accounts))
    return table


def make_operation_view(ledger):
    table = Table.grid(padding=(0, 5))
    for i, operation in reversed(
        list(enumerate(funcy.pluck_attr("operation", ledger.records), start=1))
    ):
        table.add_row(str(i), str(operation))
    return table


class CenteredPanel(Panel):
    def __init__(
        self,
        content,
        title=None,
        align_options: None | dict = None,
        panel_options: None | dict = None,
    ):
        super().__init__(
            Align(
                content,
                **({"align": "center", "vertical": "middle"} | (align_options or {})),  # type: ignore (bug in pyright?)
            ),
            title=title,
            **(panel_options or {}),
        )


def build_ledger_view():
    try:
        ledger = Ledger.load_from_file()
    except FileNotFoundError:
        return Text("no ledger file", style="red")

    layout = Layout()
    layout.split_column(
        Layout(
            CenteredPanel(make_file_info_view(ledger), title="file"),
            size=5,
        ),
        Layout(
            CenteredPanel(make_balance_view(ledger), title="balances"),
            size=7,
        ),
        Layout(
            CenteredPanel(
                make_operation_view(ledger),
                title="operations",
                align_options={"vertical": "top"},
                panel_options={"padding": (1, 0)},
            )
        ),
    )

    return layout
