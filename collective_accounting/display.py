import arrow
import funcy
from rich.align import Align
from rich.columns import Columns
from rich.console import Group
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .models import (
    AddAccount,
    AddPot,
    Ledger,
    PaysContribution,
    Reimburse,
    RemoveAccount,
    RequestContribution,
    SharedExpense,
    Transfer,
)
from .utils import file_creation_timestamp, file_modification_timestamp


def format_timestamp(timestamp) -> str:
    return arrow.get(timestamp).to("local").format("YYYY-MM-DD HH:mm:ss")


def make_file_info_view(ledger):
    file_path = Ledger.LEDGER_FILE
    return Columns(
        (
            Text(f"file:{file_path}"),
            Text(f"creation:{format_timestamp(file_creation_timestamp(file_path))}"),
            Text(
                f"last update:{format_timestamp(file_modification_timestamp(file_path))}"
            ),
        ),
        expand=True,
    )


def format_balance(balance) -> Text:
    balance_float = float(balance)
    if balance_float > 0:
        return Text(str(balance), style="green")
    elif balance_float < 0:
        return Text(str(balance), style="red")
    else:
        return Text(str(balance), style="blue")


def make_balance_display(ledger, name):
    return Text(name) + ":" + format_balance(ledger.state[name])


def make_pot_account_display(ledger):
    return f"Pot Account:{ledger.pot}"


def make_state_view(ledger):
    if ledger.state.has_pot:
        return Group(
            Columns(
                [make_balance_display(ledger, "POT"), make_pot_account_display(ledger)]
            ),
            Columns(
                make_balance_display(ledger, name)
                for name in ledger.state
                if name != "POT"
            ),
        )
    else:
        return Columns(make_balance_display(ledger, name) for name in ledger.state)


def make_operation_view(ledger) -> Table:
    table = Table.grid(padding=(0, 5))
    for i, operation in reversed(
        list(enumerate(funcy.pluck_attr("operation", ledger.records), start=1))
    ):
        match operation:
            # --- edit accounts
            case AddAccount():
                style = "cyan"
            case RemoveAccount():
                style = "cyan"
            case AddPot():
                style = "cyan"
            # --- spending and requesting money
            case SharedExpense():
                style = "yellow"
            case RequestContribution():
                style = "red"
            # --- balancing
            case Transfer():
                style = "green"
            case Reimburse():
                style = "green"
            case PaysContribution():
                style = "green"
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
    screen.split_column(
        Layout(name="main"),
        Layout(
            name="footer",
            size=1,
        ),
    )
    screen.get("main").split_row(  # type:ignore
        Layout(name="left", ratio=2),
        Layout(name="right", ratio=3),
    )

    screen.get("left").update(  # type:ignore
        CenteredPanel(make_state_view(ledger), title="Account balances")
    )
    screen.get("right").update(  # type:ignore
        CenteredPanel(
            make_operation_view(ledger),
            title="operations",
            align_options={"vertical": "top"},
            panel_options={"padding": (1, 0)},
        )
    )
    screen.get("footer").update(  # type:ignore
        make_file_info_view(ledger)
    )
    return screen
