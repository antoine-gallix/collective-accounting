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


type Changes = list[(Account, Amount)]


class Operation:
    tag: str
    changes: Changes

    def __init__(
        self, amount: Amount, credit_to: list[Account], debt_from: list[Account]
    ) -> Changes:
        individual_credit = amount / len(credit_to)
        individual_debt = -amount / len(debt_from)
        self.changes = [(creditor, individual_credit) for creditor in credit_to] + [
            (debitor, individual_debt) for debitor in debt_from
        ]
        self.tag = "Generic Operation"

    def apply(self) -> None:
        logger.info(f"applying operation: {self.tag}")
        for account, amount in self.changes:
            account.change_balance(amount)

    def revert(self) -> None:
        logger.info(f"reverting operation: {self.tag}")
        for account, amount in self.changes:
            account.change_balance(-amount)


@dataclass
class Ledger:
    accounts: list[Account] = field(default_factory=list)
    operations: list[Operation] = field(default_factory=list)
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

    def _record_operation(self, operation: Operation) -> None:
        logger.info(f"adding operation {operation.tag}")
        self.operations.append(operation)
        operation.apply()

    def record_shared_expense(self, amount: Amount, by: str):
        logger.info(f"recording shared expense: {by!r} paid {amount} for all")
        shared_expense = Operation(
            amount=amount, credit_to=self.get(by), debt_from=self.get("ALL")
        )
        self._record_operation(shared_expense)

    def record_transfer(
        self,
        amount: Amount,
        by: str,
        to: str,
    ):
        logger.info(f"recording transfer: {by!r} send {amount} to {to!r}")
        transfer = Operation(
            amount=amount, credit_to=self.get(by), debt_from=self.get(to)
        )
        self._record_operation(transfer)
