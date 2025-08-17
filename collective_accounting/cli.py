import sys

import click
from rich import print
from rich.table import Table
from rich.text import Text

import collective_accounting
from collective_accounting import logger
from collective_accounting.models import Ledger

main = click.Group()


def load_ledger():
    try:
        return collective_accounting.Ledger.load_from_file()
    except FileNotFoundError as e:
        logger.error(e)
        sys.exit()


def format_credit(credit):
    formated = Text(f"{credit:+}")
    if credit > 0:
        formated.style = "green"
    elif credit < 0:
        formated.style = "red"
    return formated


# --------------------------------


@main.command
def init():
    """Create a new empty ledger"""
    logger.info("creating new ledger")
    ledger = Ledger()
    ledger.save_to_file()


@main.command
def show():
    """Print the content of the ledger file"""
    group = load_ledger()
    table = Table(title="Ledger")
    table.add_column("Account")
    table.add_column("Balance")
    for account in group.accounts:
        table.add_row(account.name, format_credit(account.credit))
    print(table)


@main.command
@click.argument("name", type=click.STRING)
def add_user(name):
    """Adds a user to the ledger"""
    try:
        with Ledger.edit() as ledger:
            ledger.add_account(name)
    except ValueError as error:
        logger.error(error)


@main.command
@click.argument("amount", type=click.FLOAT)
@click.argument("name", type=click.STRING)
def add_shared_expense(amount, name):
    """Record an expense made by a user for the whole group

    Rebalance the ledger so to share the cost of AMOUNT paid by NAME

    Example:

    > accountant add-shared-expense 25 antoine
    """
    with Ledger.edit() as ledger:
        ledger.add_shared_expense(by=name, amount=amount)
