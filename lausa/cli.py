import time
from itertools import combinations
from operator import xor

import click
from rich import print
from rich.live import Live

from .display import (
    expense_groups_comparison,
    expense_view,
    file_modification_timestamp,
    filtered_expense_view,
    ledger_view,
    operation_table,
    state_view,
    tag_count_table,
)
from .ledger import Ledger
from .logging import logger

main = click.Group()


@main.command
def init():
    """Create a new empty ledger"""
    logger.info("creating new ledger")
    ledger = Ledger()
    ledger.save_to_file()


@main.command
def watch():
    """Print the content of the ledger file"""
    logger.remove()
    last_timestamp = file_modification_timestamp(Ledger.LEDGER_FILE)
    with Live(ledger_view(), screen=True) as live:
        while True:
            time.sleep(0.25)
            new_timestamp = file_modification_timestamp(Ledger.LEDGER_FILE)
            # one of the two timestamp is None: ledger just got deleted or created
            if xor(last_timestamp is None, new_timestamp is None) or (
                (last_timestamp and new_timestamp) and new_timestamp > last_timestamp
            ):
                last_timestamp = new_timestamp
                live.update(ledger_view())


@main.command
@click.option("--color/--no-color", default=True)
def accounts(color):
    """Print the state of the accounts"""
    if color:
        print(state_view(Ledger.load_from_file()))
    else:
        for name, account in sorted(
            Ledger.load_from_file().state.user_accounts.items(),
            key=lambda item: item[1].diff,
            reverse=True,
        ):
            print(f"{name}: {account.diff:+}")


@main.command
def operations():
    """List operations"""
    ledger = Ledger.load_from_file()
    print(operation_table(ledger.operations))


@main.group
def expenses(): ...


@expenses.command("list")
@click.option("--tag", type=click.STRING)
@click.option("--no-tag", is_flag=True)
def list_expenses(tag, no_tag):
    """List expenses

    TAG: select expenses with specified TAG
    NO_TAG: select expenses with no tag. overrides TAG option
    """
    expenses = Ledger.load_from_file().expenses
    if no_tag:
        print(filtered_expense_view(expenses, None))
    elif tag is not None:
        print(filtered_expense_view(expenses, tag))
    else:
        print(expense_view(expenses))


@expenses.command("tags")
def list_tags():
    """List tags found in ledger expenses"""
    expenses = Ledger.load_from_file().expenses
    print(tag_count_table(expenses))


@expenses.command("compare")
@click.argument("tags", type=click.STRING, nargs=-1)
def compare_expenses(tags):
    """Compare expenses"""
    expenses = Ledger.load_from_file().expenses
    print(expense_groups_comparison(expenses, tags))


# ------------------------ operations ------------------------


@main.command
@click.option("--index", type=click.INT)
def undo(index):
    """Undo operation

    By default undo last operation

    INDEX: undo operation at given index
    """
    with Ledger.edit() as ledger:
        if index is not None:
            ledger.records.pop(index - 1)
        else:
            ledger.records.pop()


@main.group
def record():
    """[Record operations]"""
    pass


@record.command
@click.argument("name", type=click.STRING)
def add_user(name):
    """Adds a user to the ledger"""
    try:
        with Ledger.edit() as ledger:
            ledger.add_account(name)
    except (ValueError, RuntimeError) as error:
        logger.error(error)


@record.command
def add_pot():
    """Setup shared pot for ledger"""
    try:
        with Ledger.edit() as ledger:
            ledger.add_pot()
    except (ValueError, RuntimeError) as error:
        logger.error(error)


@record.command("expense")
@click.argument("amount", type=click.FLOAT)
@click.argument("name", type=click.STRING)
@click.argument("subject", type=click.STRING)
def record_shared_expense(amount, name, subject):
    """Record an expense made by a user for the whole group

    Rebalance the ledger so to share the cost of AMOUNT paid by NAME

    Example:

    > accountant record-shared-expense 25 antoine "buy wood"
    """
    with Ledger.edit() as ledger:
        ledger.record_shared_expense(amount, name, subject)


@record.command("transfer")
@click.argument("amount", type=click.FLOAT)
@click.argument("by", type=click.STRING)
@click.argument("to", type=click.STRING)
def record_transfer(amount, by, to):
    """Record money transfered from a user to another

    Rebalance the ledger so to share the cost of AMOUNT paid by NAME

    Example:

    > accountant record-transfer 10 baptiste antoine
    """
    with Ledger.edit() as ledger:
        ledger.record_transfer(amount=amount, by=by, to=to)


@record.command("transfer-debt")
@click.argument("amount", type=click.FLOAT)
@click.argument("origin", type=click.STRING)
@click.argument("to", type=click.STRING)
def record_transfer_debt(amount, origin, to):
    """Record debt transfered from a user to another"""
    with Ledger.edit() as ledger:
        ledger.record_transfer_debt(amount=amount, old_debitor=origin, new_debitor=to)


@record.command("debt")
@click.argument("amount", type=click.FLOAT)
@click.argument("debitor", type=click.STRING)
@click.argument("creditor", type=click.STRING)
@click.argument("subject", type=click.STRING)
def record_debt(amount, debitor, creditor, subject):
    """Record debt between two users"""
    with Ledger.edit() as ledger:
        ledger.record_debt(
            amount=amount, debitor=debitor, creditor=creditor, subject=subject
        )


# ------------------------ pot operations ------------------------


@record.command("request-contribution")
@click.argument("amount", type=click.FLOAT)
def record_request_contribution(amount):
    """Request contribution from all account for the pot"""
    with Ledger.edit() as ledger:
        ledger.request_contribution(amount)


@record.command("contribution")
@click.argument("amount", type=click.FLOAT)
@click.argument("name", type=click.STRING)
def record_contribution(amount, name):
    """Record user sending money to the pot"""
    with Ledger.edit() as ledger:
        ledger.pays_contribution(amount, name)


@record.command
@click.argument("amount", type=click.FLOAT)
@click.argument("name", type=click.STRING)
def reimburse(amount, name):
    """Record money reimbursed from the pot to a user"""
    with Ledger.edit() as ledger:
        ledger.reimburse(amount, name)
