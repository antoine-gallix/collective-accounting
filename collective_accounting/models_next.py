import pathlib
from abc import ABC, abstractmethod
from copy import copy
from dataclasses import asdict, dataclass, field
from decimal import Decimal
from typing import ClassVar, Collection, Dict, Self

import funcy
import yaml

from .logging import logger
from .utils import Amount, divide

type Name = str


class AtomicChange(ABC):
    """An AtomicChange is a change of state that cannot be decomposed in multiple smaller operations."""


@dataclass
class AccountCreation(AtomicChange):
    name: Name


@dataclass
class AccountRemoval(AtomicChange):
    name: Name


@dataclass
class BalanceChange(AtomicChange):
    name: Name
    amount: Amount


type ChangeSet = Collection[AtomicChange]


@dataclass
class LedgerState(Dict[str, Decimal]):
    """A collection of accounts with a balance. Represents the state of a ledger at a given point in time."""

    def _add_account(self, name: str):
        if not isinstance(name, str):
            raise TypeError(f"name is not a string: {name}")
        if not name:
            raise ValueError(f"name string is empty: {name}")
        if name in self:
            raise RuntimeError(f"account already exists: {name}")
        self[name] = Decimal(0)

    def _remove_account(self, name: str):
        if name not in self:
            raise RuntimeError(f"account does not exists: {name} ")
        if self[name] != 0:
            raise RuntimeError(f"account has non-null balance: {name}")
        del self[name]

    def _change_balance(self, name: str, amount: Amount):
        logger.info(f"changing balance of {name!r}: {amount:+}")
        try:
            self[name] += Decimal(amount)
        except KeyError:
            raise RuntimeError(f"account with name {name} does not exists")

    def _check_balances(self):
        if (error := sum(self.values())) != 0:
            raise RuntimeError(f"accounts unbalanced. Sum of balances is {error:+}")

    # -------- changes

    def apply_change(self, change: AtomicChange):
        match change:
            case AccountCreation():
                self._add_account(change.name)
            case AccountRemoval():
                self._remove_account(change.name)
            case BalanceChange():
                self._change_balance(change.name, change.amount)

    def apply_changeset(self, change_set: ChangeSet) -> Self:
        next_state = copy(self)
        for change in change_set:
            next_state.apply_change(change)
        next_state._check_balances()
        return next_state


@dataclass
class Operation(ABC):
    """An Operation is an action that transforms the ledger state. An operation applied to a ledger, if valid, produces a changeset that then modifies the state of the ledger."""

    TYPE: ClassVar[str]

    @property
    @abstractmethod
    def description(self) -> str: ...

    @abstractmethod
    def changes(self, accounts: LedgerState) -> ChangeSet: ...

    def as_dict(self) -> dict:
        return {"operation": self.TYPE} | asdict(self)


@dataclass
class AddAccount(Operation):
    TYPE: ClassVar[str] = "Add Account"
    name: Name

    @property
    def description(self):
        return self.name

    def changes(self, accounts: LedgerState):
        return [AccountCreation(self.name)]


@dataclass
class RemoveAccount(Operation):
    TYPE: ClassVar[str] = "Remove Account"
    name: Name

    @property
    def description(self):
        return self.name

    def changes(self, accounts: LedgerState):
        return [AccountRemoval(self.name)]


@dataclass
class ChangeBalances(Operation):
    """Generic Balance Change Operation

    Represents the transfer of credit from one group of accounts to another group of accounts. The amount of the change is divided between the creditors (add_to), and added to their balance; between the debitors (substract_from), it is divided and substracted from their balance.

    Specifying None for either group is interpreted as `all accounts`

    More precisely:
        individual_creditor_balance_change = amount / len(add_to)
        individual_debitor_balance_change = - amount / len(substract_from)
    """

    TYPE: ClassVar[str] = "Change Balances"
    amount: Amount
    credit_to: Collection[Name] | None
    debt_from: Collection[Name] | None

    @property
    def description(self):
        return f"transfering credit ({self.amount}) from ({'All' if self.debt_from is None else ', '.join(self.debt_from)}) to ({'All' if self.credit_to is None else ', '.join(self.credit_to)})"

    def changes(self, accounts: LedgerState) -> ChangeSet:
        creditors = list(accounts.keys()) if self.credit_to is None else self.credit_to
        debitors = list(accounts.keys()) if self.debt_from is None else self.debt_from
        return [
            BalanceChange(name=creditor, amount=balance_change)
            for creditor, balance_change in zip(
                creditors, divide(self.amount, len(creditors))
            )
        ] + [
            BalanceChange(name=debitor, amount=-balance_change)
            for debitor, balance_change in zip(
                debitors, divide(self.amount, len(debitors))
            )
        ]


@dataclass
class SharedExpense(Operation):
    TYPE: ClassVar[str] = "Shared Expense"
    amount: Amount
    by: Name
    subject: str

    @property
    def description(self):
        return f"{self.by} paid {self.amount} for {self.subject}"

    def changes(self, accounts: LedgerState):
        return ChangeBalances(
            credit_to=[self.by], debt_from=None, amount=self.amount
        ).changes(accounts)


@dataclass
class Transfer(Operation):
    TYPE: ClassVar[str] = "Money Transfer"
    amount: Amount
    by: Name
    to: Name

    @property
    def description(self):
        return f"{self.by} sends {self.amount} to {self.to}"

    def changes(self, accounts: LedgerState):
        return ChangeBalances(
            credit_to=[self.by], debt_from=[self.to], amount=self.amount
        ).changes(accounts)


@dataclass
class LedgerRecord:
    state: LedgerState
    operation: Operation
    changes: ChangeSet


@dataclass
class Ledger:
    records: list[LedgerRecord] = field(default_factory=list)
    LEDGER_FILE = "ledger.pkl"

    @property
    def state(self):
        if not self.records:
            return LedgerState()
        else:
            return self.records[-1].state

    def save_to_file(self):
        pathlib.Path(self.LEDGER_FILE).write_text(
            yaml.dump_all(
                funcy.map(
                    Operation.as_dict, funcy.pluck_attr("operation", self.records)
                ),
                sort_keys=False,
            )
        )

    @classmethod
    def load_from_file(cls):
        # load operations from files
        # update state to the latest operation
        ...

    def record_operation(self, operation):
        logger.info(f"recording operation into ledger: {operation}")
        try:
            changes = operation.changes(self.state)
            new_state = self.state.apply_changeset(changes)
        except:
            logger.error("operation could not been applied")
            raise
        self.records.append(
            LedgerRecord(operation=operation, changes=changes, state=new_state)
        )
