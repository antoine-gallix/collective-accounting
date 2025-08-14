import click
import collective_accounting
from collective_accounting import logger
import sys

main = click.Group()


@main.command
def show():
    """Show ledger in it's current state"""
    try:
        group = collective_accounting.Group.import_()
    except FileNotFoundError as e:
        logger.error(e)
        sys.exit()
    for account in group.accounts:
        print(account)


if __name__ == "__main__":
    # call the main group
    main()
