import click
import collective_accounting
from collective_accounting import logger
import sys
from rich import print
from rich.table import Table
from rich.text import Text

main = click.Group()


def load_group():
    try:
        return collective_accounting.Group.import_()
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


@main.command
def show():
    """Show ledger in it's current state"""
    group = load_group()
    table = Table(title="Ledger")
    table.add_column("Account")
    table.add_column("Balance")
    for account in group.accounts:
        table.add_row(account.name, format_credit(account.credit))
    print(table)


if __name__ == "__main__":
    # call the main group
    main()
