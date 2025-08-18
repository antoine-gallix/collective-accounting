import time
from operator import xor

import click
from rich import print
from rich.live import Live

from collective_accounting import logger
from collective_accounting.models import Ledger
from collective_accounting.utils import build_ledger_table, timestamp

main = click.Group()


@main.command
def init():
    """Create a new empty ledger"""
    logger.info("creating new ledger")
    ledger = Ledger()
    ledger.save_to_file()


@main.command
def show():
    """Print the content of the ledger file"""
    table = build_ledger_table()
    print(table)


@main.command
def watch():
    """Print the content of the ledger file"""
    logger.remove()
    last_timestamp = timestamp(Ledger.LEDGER_FILE)
    with Live(build_ledger_table(), screen=True, auto_refresh=False) as live:
        while True:
            time.sleep(0.25)
            new_timestamp = timestamp(Ledger.LEDGER_FILE)
            # one of the two timestamp is None: ledger just got deleted or created
            if xor(last_timestamp is None, new_timestamp is None) or (
                (last_timestamp and new_timestamp) and new_timestamp > last_timestamp
            ):
                last_timestamp = new_timestamp
                live.update(build_ledger_table(), refresh=True)


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
def record_shared_expense(amount, name):
    """Record an expense made by a user for the whole group

    Rebalance the ledger so to share the cost of AMOUNT paid by NAME

    Example:

    > accountant record-shared-expense 25 antoine
    """
    with Ledger.edit() as ledger:
        ledger.record_shared_expense(amount=amount, by=name)


@main.command
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
