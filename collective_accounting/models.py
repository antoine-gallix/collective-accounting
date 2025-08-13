from dataclasses import dataclass, field
from .logging import logger
import funcy
import pickle
import pathlib


@dataclass
class Account:
    name: str
    credit: float = 0

    def change_credit(self, change: int | float):
        logger.info(f"applying {change:+.2f} credit change to account {self.name!r}")
        self.credit += change


@dataclass
class Group:
    accounts: list[Account] = field(default_factory=list)
    LEDGER_FILE = "ledger.pkl"

    def export(self):
        logger.info(f"exporting group to file: {self.LEDGER_FILE}")
        with pathlib.Path(self.LEDGER_FILE).open("wb") as ledger_file:
            pickle.dump(self, ledger_file)

    @classmethod
    def from_file(cls):
        logger.info(f"exporting group to file: {cls.LEDGER_FILE}")
        with pathlib.Path(cls.LEDGER_FILE).open("rb") as ledger_file:
            return pickle.load(ledger_file)

    def as_dict(self):
        return {account.name: account.credit for account in self.accounts}

    def get(self, name):
        account = funcy.first(
            funcy.filter(lambda account: account.name == name, self.accounts)
        )
        if not account:
            logger.error("no account with name {name}")
            raise KeyError
        return account

    def add_account(self, name):
        logger.info(f"creating new account: {name!r}")
        account = Account(name)
        self.accounts.append(account)
        return account

    def add_shared_expense(self, name, value):
        logger.info(f"add shared expense of {value} from: {name!r}")
        credited_account, debited_accounts = funcy.lsplit(
            lambda account: account.name == name, self.accounts
        )
        individual_share = value / len(self.accounts)
        logger.debug("individual share of the expense: ")
        credited_account[0].change_credit(value - individual_share)
        for debited_account in debited_accounts:
            debited_account.change_credit(-individual_share)
