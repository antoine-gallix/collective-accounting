import arrow
import funcy
from rich.align import Align
from rich.columns import Columns
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .models import (
    AddAccount,
    AddPot,
    Ledger,
    Reimburse,
    RemoveAccount,
    RequestContribution,
    SharedExpense,
    Transfer,
)
from .utils import file_creation_timestamp, file_modification_timestamp


def format_timestamp(timestamp) -> str:
    return arrow.get(timestamp).to("local").format("YYYY-MM-DD HH:mm:ss")


def make_file_info_view(ledger) -> Table:
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


def format_balance(balance) -> Text:
    balance_float = float(balance)
    if balance_float > 0:
        return Text(f"{balance:+.2f}", style="green")
    elif balance_float < 0:
        return Text(f"{balance:+.2f}", style="red")
    else:
        return Text(str(balance), style="blue")


def make_balance_chip(ledger, name):
    return Panel((Text(name) + ":" + format_balance(ledger.state[name])))


def make_balance_view(ledger) -> Columns:
    return Columns(make_balance_chip(ledger, name) for name in ledger.state)


def make_operation_view(ledger) -> Table:
    table = Table.grid(padding=(0, 5))
    for i, operation in reversed(
        list(enumerate(funcy.pluck_attr("operation", ledger.records), start=1))
    ):
        match operation:
            case AddAccount():
                style = "cyan"
            case RemoveAccount():
                style = "cyan"
            case AddPot():
                style = "cyan"
            # ---
            case Transfer():
                style = "green"
            case SharedExpense():
                style = "yellow"
            case Reimburse():
                style = "green"
            case RequestContribution():
                style = "red"
            case _:
                style = ""
        table.add_row(
            str(i),
            Text(operation.TYPE, style=style),
            operation.description,
        )
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

    screen = Layout()
    screen.split_row(
        Layout(name="left", ratio=2),
        Layout(
            name="right",
            ratio=3,
        ),
    )
    screen.get("left").split_column(  # type:ignore
        Layout(
            name="left_top",
            size=5,
        ),
        Layout(
            name="left_bottom",
        ),
    )

    screen.get("right").update(  # type:ignore
        CenteredPanel(
            make_operation_view(ledger),
            title="operations",
            align_options={"vertical": "top"},
            panel_options={"padding": (1, 0)},
        )
    )
    screen.get("left_top").update(  # type:ignore
        CenteredPanel(make_file_info_view(ledger), title="file")
    )
    screen.get("left_bottom").update(  # type:ignore
        CenteredPanel(make_balance_view(ledger), title="balances")
    )
    return screen
