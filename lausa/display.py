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


def file_info_view(ledger):
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


def diff_style(balance) -> Text:
    balance_float = float(balance)
    if balance_float > 0:
        return Text(format(balance, "+"), style="green")
    elif balance_float < 0:
        return Text(format(balance, "+"), style="red")
    else:
        return Text(str(balance), style="blue")


def diff_display(ledger, name):
    return Text(name) + ":" + diff_style(ledger.state[name].diff)


def pot_state_table(ledger):
    table = Table.grid(padding=(0, 2), expand=True)
    table.add_row("Pot Balance", Text(str(ledger.state.pot.balance), style="blue"))
    table.add_row("Pot Diff", diff_style(ledger.state.pot.diff))

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


def accounts_table(ledger):
    table = Table.grid(padding=(0, 2), expand=True)
    for name, account in sorted(
        ledger.state.user_accounts.items(),
        key=lambda item: item[1].diff,
        reverse=True,
    ):
        table.add_row(name, diff_style(account.diff))
    return table


def state_view(ledger):
    if ledger.state.has_pot:
        return Group(
            pot_state_table(ledger),
            Rule(),
            accounts_table(ledger),
        )
    else:
        return accounts_table(ledger)


def operation_name_style(operation):
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


def name_display(name: Name):
    return Text(name, style="blue")


def money_display(amount: Money):
    return Text(str(amount), style="green")


def text_display(text: str):
    return Text(text, style="yellow")


def tag_display(text: str):
    return Text(text, style="magenta")


def tags_display(tags):
    return Text.assemble("", *funcy.interpose(", ", [tag_display(t) for t in tags]))


def operation_description(operation) -> Text:
    match operation:
        case AddAccount():
            return name_display(operation.name)
        case RemoveAccount():
            return name_display(operation.name)
        case AddPot():
            return Text("Add a common pot to the group")
        # --- money movement
        case SharedExpense():
            description = Text.assemble(
                "",
                name_display(operation.payer),
                " pays ",
                money_display(operation.amount),
                " for ",
                text_display(operation.subject),
            )
            if operation.tags:
                description += Text.assemble(
                    " [",
                    tags_display(operation.tags),
                    "]",
                )

            return description
        case Transfer():
            return Text.assemble(
                Text()
                + name_display(operation.sender)
                + Text(" sends ")
                + money_display(operation.amount)
                + Text(" to ")
                + name_display(operation.receiver),
            )
        case Reimburse():
            return (
                Text("Reimburse ")
                + money_display(operation.amount)
                + Text(" to ")
                + name_display(operation.receiver)
                + Text(" from the pot")
            )
        case PaysContribution():
            return (
                Text()
                + name_display(operation.sender)
                + Text(" contributes ")
                + money_display(operation.amount)
                + Text(" to the pot")
            )
        # --- debt movement
        case Debt():
            return (
                Text()
                + name_display(operation.debitor)
                + " owes "
                + money_display(operation.amount)
                + " to "
                + name_display(operation.creditor)
                + " for "
                + text_display(operation.subject)
            )
        case RequestContribution():
            return (
                Text("Request contribution of ")
                + money_display(operation.amount)
                + Text(" from everyone")
            )
        case TransferDebt():
            return (
                Text()
                + name_display(operation.new_debitor)
                + Text(" covers ")
                + money_display(operation.amount)
                + Text(" of debt from ")
                + name_display(operation.old_debitor)
            )
        case _:
            return Text()


def ledger_summary_view(ledger):
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


def operation_table(operations):
    table = Table.grid(padding=(0, 2))
    for i, operation in reversed(list(enumerate(operations, start=1))):
        table.add_row(
            str(i),
            operation_name_style(operation),
            operation_description(operation),
        )
    return table


def expense_table(expenses: list[SharedExpense]):
    if not expenses:
        return Text("no expense to display", style="red")
    table = Table()
    table.add_column("payer")
    table.add_column("amount")
    table.add_column("subject")
    table.add_column("tags")
    for expense in reversed(expenses):
        table.add_row(
            name_display(expense.payer),
            money_display(expense.amount),
            expense.subject,
            tags_display(expense.tags),
        )
    return table


def expense_summary(expenses):
    return Group(
        Text.assemble("count: ", (str(len(expenses)), "blue")),
        Text.assemble(
            "total: ",
            (
                # specifying null money for start avoids downcasting result to Decimal
                str(expenses.sum()),
                "blue",
            ),
        ),
    )


def expense_view(expenses):
    return Group(expense_summary(expenses), Rule(), expense_table(expenses))


def comparative_expense_summary(filtered_expenses, expenses):
    return Group(
        Text.assemble(
            "count: ",
            (str(len(filtered_expenses)), "blue"),
            "/",
            (str(len(expenses)), "green"),
        ),
        Text.assemble(
            "total: ",
            "count: ",
            (str(filtered_expenses.sum()), "blue"),
            "/",
            (str(expenses.sum()), "green"),
        ),
    )


def comparative_expense_view(expenses, tag):
    filtered_expenses = expenses.filter(tag)
    return Group(
        Text.assemble(
            "tag filter: ", Text("no tag" if tag is None else tag, style="magenta")
        ),
        comparative_expense_summary(filtered_expenses, expenses),
        Rule(),
        expense_table(filtered_expenses),
    )


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


def ledger_view():
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
        CenteredPanel(ledger_summary_view(ledger), title="Summary")
    )
    screen.get("accounts").update(  # type:ignore
        CenteredPanel(state_view(ledger), title="Accounts")
    )
    screen.get("right").update(  # type:ignore
        CenteredPanel(
            operation_table(ledger.operations),
            title="operations",
            align_options={"vertical": "top"},
            panel_options={"padding": (1, 0)},
        )
    )
    screen.get("footer").update(  # type:ignore
        file_info_view(ledger)
    )
    return screen
