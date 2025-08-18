import pathlib
import pickle
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Literal, Self

import funcy

from .logging import logger

type AccountSelector = Literal["ALL"] | str | list[str]
type Amount = int | float


@dataclass
class Account:
    name: str
    balance: float = 0

    def change_balance(self, change: int | float):
        logger.info(f"credit change: {self.name!r} {change:+.2f}")
        self.balance += change


@dataclass
class Ledger:
    accounts: list[Account] = field(default_factory=list)
    LEDGER_FILE = "ledger.pkl"

    def as_dict(self) -> dict:
        return {account.name: account.balance for account in self.accounts}

    # IOs

    def save_to_file(self) -> None:
        logger.info(f"writing ledger to file: {self.LEDGER_FILE}")
        with pathlib.Path(self.LEDGER_FILE).open("wb") as ledger_file:
            pickle.dump(self, ledger_file)

    @classmethod
    def load_from_file(cls):
        logger.info(f"loading ledger from file: {cls.LEDGER_FILE}")
        try:
            with pathlib.Path(cls.LEDGER_FILE).open("rb") as ledger_file:
                return pickle.load(ledger_file)
        except FileNotFoundError as e:
            raise FileNotFoundError("could not find ledger file") from e

    @classmethod
    @contextmanager
    def edit(cls) -> Self:
        ledger = cls.load_from_file()
        yield ledger
        ledger.save_to_file()

    # Account Management

    def _get_one(self, name: str) -> Account:
        """Get account by name"""
        account = funcy.first(
            funcy.filter(lambda account: account.name == name, self.accounts)
        )
        if not account:
            raise KeyError(f"no account with name {name}")
        return account

    def get(self, selector: AccountSelector) -> list[Account]:
        """Get accounts"""
        match selector:
            case "ALL":
                return self.accounts
            case str(account):
                return [self._get_one(account)]
            case [*names]:
                return [self._get_one(name) for name in names]

    def add_account(self, name: str) -> None:
        logger.info(f"creating new account: {name!r}")
        try:
            self._get_one(name)
            raise ValueError(f"account named {name!r} already exist")
        except KeyError:
            account = Account(name)
            self.accounts.append(account)
            return account

    # Changing balances

    def _credit(
        self,
        value: Amount,
        credit_to: AccountSelector = "ALL",
        debt_from: AccountSelector = "ALL",
    ) -> None:
        """Main function to change balance of accounts"""
        creditors = self.get(credit_to)
        debitors = self.get(debt_from)
        credited_value = value / len(creditors)
        for creditor in creditors:
            creditor.change_balance(credited_value)
        debited_value = value / len(debitors)
        for debitor in debitors:
            debitor.change_balance(-debited_value)

    def add_shared_expense(self, by: str, amount: Amount):
        logger.info(f"adding shared expense: {by!r} paid {amount} for all")
        self._credit(amount, credit_to=by)
