from dataclasses import dataclass, field
from decimal import Decimal
from typing import ClassVar, Dict

from .logging import logger

type Amount = Decimal | int


@dataclass
class Accounts(Dict[str, Decimal]):
    def add_account(self, name: str):
        if not isinstance(name, str):
            raise TypeError(f"name is not a string: {name}")
        if not name:
            raise ValueError(f"name string is empty: {name}")
        if name in self:
            raise ValueError(f"account with name {name} already exists")
        self[name] = Decimal(0)

    def change_balance(self, name: str, amount: Amount):
        logger.info(f"changing balance of {name!r}: {amount:+}")
        try:
            self[name] += Decimal(amount)
        except KeyError:
            raise ValueError(f"account does not exist: {name}")

    def check_balances(self):
        if (error := sum(self.values())) != 0:
            raise RuntimeError(f"accounts unbalanced. Sum of balances is {error:+}")


@dataclass
class Operation:
    TYPE: ClassVar[str] = "Base Operation"
    params: dict = field(default=dict)

    def __init__(self, **params):
        self.params = params

    @property
    def description(self):
        return "nothing happens"

    def apply(self, accounts: Accounts): ...
    def revert(self, accounts: Accounts): ...


@dataclass
class AddAccount(Operation):
    TYPE: ClassVar[str] = "Add Account"

    @property
    def description(self):
        return "name"

    def apply(self, accounts: Accounts): ...
    def revert(self, accounts: Accounts): ...


@dataclass
class Ledger:
    accounts: Accounts = field(default_factory=Accounts)
    operations: list[Operation] = field(default_factory=list)
    LEDGER_FILE = "ledger.pkl"
