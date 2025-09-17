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

from .account import Name
from .ledger import Ledger
from .money import Money
from .operations import (
    AddAccount,
    AddPot,
    Debt,
    PaysContribution,
    Reimburse,
    RemoveAccount,
    RequestContribution,
    SharedExpense,
    Transfer,
    TransferDebt,
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
            Text("file: ") + Text(f"{file_path}", style="blue"),
            Text("creation: ")
            + Text(
                format_timestamp(file_creation_timestamp(file_path)),
                style="blue",
            ),
            Text("last update: ")
            + Text(
                format_timestamp(file_modification_timestamp(file_path)),
                style="blue",
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
    table.add_row("Pot Balance", Text(str(ledger.state.pot.balance), style="blue"))
    table.add_row("Pot Diff", format_diff(ledger.state.pot.diff))

    if (pot_expected_balance := ledger.state.pot.balance + ledger.state.pot.diff) < 0:
        table.add_row(
            "Expected Pot Deficit",
            Text(str(-pot_expected_balance), style="red"),
        )
    elif pot_expected_balance > 0:
        table.add_row(
            "Expected Pot Excedent",
            Text(str(pot_expected_balance), style="green"),
        )
    else:
        table.add_row("Expected Pot State", Text("0"), style="green")
    return table


def make_accounts_table(ledger):
    table = Table.grid(padding=(0, 2), expand=True)
    for name, account in sorted(
        ledger.state.user_accounts.items(),
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


def style_operation_name(operation):
    match operation:
        # --- edit accounts
        case AddAccount():
            style = "cyan"
        case RemoveAccount():
            style = "cyan"
        case AddPot():
            style = "cyan"
        # --- money movement
        case SharedExpense():
            style = "red"
        case Transfer():
            style = "red"
        case Reimburse():
            style = "red"
        case PaysContribution():
            style = "red"
        # --- debt movement
        case RequestContribution():
            style = "blue"
        case Debt():
            style = "blue"
        case TransferDebt():
            style = "blue"
        case _:
            style = ""
    return Text(operation.__class__.__name__, style=style)


def style_name(name: Name):
    return Text(name, style="blue")


def style_money(amount: Money):
    return Text(str(amount), style="green")


def style_text(text: str):
    return Text(text, style="yellow")


def describe_operation(operation) -> Text:
    match operation:
        case AddAccount():
            return style_name(operation.name)
        case RemoveAccount():
            return style_name(operation.name)
        case AddPot():
            return Text("Add a common pot to the group")
        # --- money movement
        case SharedExpense():
            return Text.assemble(
                Text(),
                style_name(operation.payer),
                Text(" pays "),
                style_money(operation.amount),
                Text(" for "),
                style_text(operation.subject),
            )
        case Transfer():
            return Text.assemble(
                Text()
                + style_name(operation.sender)
                + Text(" sends ")
                + style_money(operation.amount)
                + Text(" to ")
                + style_name(operation.receiver),
            )
        case Reimburse():
            return (
                Text("Reimburse ")
                + style_money(operation.amount)
                + Text(" to ")
                + style_name(operation.receiver)
                + Text(" from the pot")
            )
        case PaysContribution():
            return (
                Text()
                + style_name(operation.sender)
                + Text(" contributes ")
                + style_money(operation.amount)
                + Text(" to the pot")
            )
        # --- debt movement
        case Debt():
            return (
                Text()
                + style_name(operation.debitor)
                + " owes "
                + style_money(operation.amount)
                + " to "
                + style_name(operation.creditor)
                + " for "
                + style_text(operation.subject)
            )
        case RequestContribution():
            return (
                Text("Request contribution of ")
                + style_money(operation.amount)
                + Text(" from everyone")
            )
        case TransferDebt():
            return (
                Text()
                + style_name(operation.new_debitor)
                + Text(" covers ")
                + style_money(operation.amount)
                + Text(" of debt from ")
                + style_name(operation.old_debitor)
            )
        case _:
            return ""


def make_summary_view(ledger):
    table = Table.grid(padding=(0, 2))
    table.add_row("users", Text(str(len(ledger.state.user_accounts)), style="blue"))
    table.add_row(
        "pot", Text("yes", style="blue") if ledger.state.has_pot else Text("no")
    )
    table.add_row(
        "expenses",
        Text(
            str(
                -sum(
                    (account.balance for account in ledger.state.user_accounts.values())
                )
            ),
            style="yellow",
        ),
    )
    return table


def make_operation_view(ledger) -> Table:
    table = Table.grid(padding=(0, 2))
    for i, operation in reversed(list(enumerate(ledger.operations, start=1))):
        table.add_row(
            str(i),
            style_operation_name(operation),
            describe_operation(operation),
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
    screen.get("left").split_column(  # type:ignore
        Layout(name="summary", size=5), Layout(name="accounts")
    )
    screen.get("summary").update(  # type:ignore
        CenteredPanel(make_summary_view(ledger), title="Summary")
    )
    screen.get("accounts").update(  # type:ignore
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
