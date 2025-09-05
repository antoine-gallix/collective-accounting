import time
from operator import xor

import click
from rich.live import Live

from .display import build_ledger_view
from .logging import logger
from .models import Ledger
from .utils import file_modification_timestamp

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
    with Live(build_ledger_view(), screen=True) as live:
        while True:
            time.sleep(0.25)
            new_timestamp = file_modification_timestamp(Ledger.LEDGER_FILE)
            # one of the two timestamp is None: ledger just got deleted or created
            if xor(last_timestamp is None, new_timestamp is None) or (
                (last_timestamp and new_timestamp) and new_timestamp > last_timestamp
            ):
                last_timestamp = new_timestamp
                live.update(build_ledger_view())


@main.command
@click.argument("name", type=click.STRING)
def add_user(name):
    """Adds a user to the ledger"""
    try:
        with Ledger.edit() as ledger:
            ledger.add_account(name)
    except (ValueError, RuntimeError) as error:
        logger.error(error)


@main.command
def add_pot():
    """Setup shared pot for ledger"""
    try:
        with Ledger.edit() as ledger:
            ledger.add_pot()
    except (ValueError, RuntimeError) as error:
        logger.error(error)


@main.command
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


@main.command
@click.argument("amount", type=click.FLOAT)
@click.argument("name", type=click.STRING)
def reimburse(amount, name):
    """Record money reimbursed from the pot to a user"""
    with Ledger.edit() as ledger:
        ledger.reimburse(amount, name)


@main.command
@click.argument("amount", type=click.FLOAT)
def request_contribution(amount):
    """Request contribution from all account for the pot"""
    with Ledger.edit() as ledger:
        ledger.request_contribution(amount)


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
