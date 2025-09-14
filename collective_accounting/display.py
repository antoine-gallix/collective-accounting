import pathlib

import arrow
import funcy
from rich.align import Align
from rich.columns import Columns
from rich.console import Group
from rich.layout import Layout
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from .ledger import Ledger
from .operations import (
    AddAccount,
    AddPot,
    PaysContribution,
    Reimburse,
    RemoveAccount,
    RequestContribution,
    SharedExpense,
    Transfer,
)


@funcy.ignore(FileNotFoundError)
def file_modification_timestamp(path):
    return pathlib.Path(path).stat().st_mtime


@funcy.ignore(FileNotFoundError)
def file_creation_timestamp(path):
    return pathlib.Path(path).stat().st_atime


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


def format_diff(balance) -> Text:
    balance_float = float(balance)
    if balance_float > 0:
        return Text(format(balance, "+"), style="green")
    elif balance_float < 0:
        return Text(format(balance, "+"), style="red")
    else:
        return Text(str(balance), style="blue")


def make_diff_display(ledger, name):
    return Text(name) + ":" + format_diff(ledger.state[name].diff)


def make_pot_state(ledger):
    table = Table.grid(padding=(0, 2), expand=True)
    table.add_row("Pot Balance", str(ledger.state.pot.balance))
    table.add_row("Pot Diff", format_diff(ledger.state.pot.diff))
    return table


def make_accounts_table(ledger):
    table = Table.grid(padding=(0, 2), expand=True)
    for name, account in sorted(
        ledger.state.user_accounts,
        key=lambda item: item[1].diff,
        reverse=True,
    ):
        table.add_row(name, format_diff(account.diff))
    return table


def make_state_view(ledger):
    if ledger.state.has_pot:
        return Group(
            make_pot_state(ledger),
            Rule(),
            make_accounts_table(ledger),
        )
    else:
        return make_accounts_table(ledger)


def make_operation_view(ledger) -> Table:
    table = Table.grid(padding=(0, 2))
    for i, operation in reversed(list(enumerate(ledger.operations, start=1))):
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
            Text(operation.__class__.__name__, style=style),
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
        CenteredPanel(make_state_view(ledger), title="Accounts")
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
