import pathlib
from abc import ABC, abstractmethod
from contextlib import contextmanager
from copy import copy
from dataclasses import asdict, dataclass, field
from typing import (
    ClassVar,
    Collection,
    DefaultDict,
    Dict,
    Literal,
    Mapping,
    Self,
)

import funcy
import yaml

from .logging import logger
from .utils import Money

type Name = str
type AccountAction = Literal["Create"] | Literal["Remove"]
type BalanceChange = Money
type Change = AccountAction | BalanceChange
type ChangeSet = Mapping[Name, Change]


class LedgerState(Dict[str, Money]):
    """A collection of accounts with a balance. Represents the state of a ledger at a given point in time.

    Operations on a ledger state are:
    - addition and removal of accounts
    - application of balanced changes to accounts

    LedgerState will raise Exceptions in the following cases:
    - add an account with name that is not a string
    - add an account with name that is empty
    - add an account with name that already exists
    - remove an account that does not exist
    - remove an account that does not have a null balance
    """

    def __str__(self):
        return super().__str__()

    @property
    def has_pot(self):
        return "POT" in self

    # ---

    def _add_account(self, name: str):
        if not isinstance(name, str):
            raise TypeError(f"name is not a string: {name}")
        if not name:
            raise ValueError(f"name string is empty: {name}")
        if name in self:
            raise RuntimeError(f"account already exists: {name}")
        self[name] = Money(0)

    def _remove_account(self, name: str):
        if name not in self:
            raise RuntimeError(f"account does not exists: {name} ")
        if self[name] != 0:
            raise RuntimeError(f"account has non-null balance: {name}")
        del self[name]

    def _change_balance(self, name: str, amount: Money):
        logger.debug(f"balance change: {name!r} {amount:+}")
        try:
            self[name] += amount
        except KeyError:
            raise RuntimeError(f"account with name {name} does not exists")

    def _check_balances(self):
        if (error := sum(self.values())) != 0:
            raise RuntimeError(f"accounts unbalanced. Sum of balances is {error:+}")

    # -------- changes

    def _apply_change(self, name: Name, change: Change):
        match change:
            case "Create":
                self._add_account(name)
            case "Remove":
                self._remove_account(name)
            case Money():
                self._change_balance(name, change)

    def apply_changeset(self, change_set: ChangeSet) -> Self:
        next_state = copy(self)
        for name, change in change_set.items():
            next_state._apply_change(name, change)
        next_state._check_balances()
        return next_state


@dataclass
class Operation(ABC):
    """An Operation is an action that transforms the ledger state. An operation applied to a ledger, if valid, produces a changeset that then modifies the state of the ledger."""

    TYPE: ClassVar[str]

    def __str__(self):
        return f"{self.TYPE}: {self.description}"

    @property
    def description(self) -> str: ...

    @abstractmethod
    def changes(self, state: LedgerState) -> ChangeSet: ...


@dataclass
class AddAccount(Operation):
    TYPE: ClassVar[str] = "Add Account"
    name: Name

    @property
    def description(self):
        return self.name

    def changes(self, state: LedgerState):  # type:ignore
        if self.name == "POT":
            raise ValueError("'POT' is a reserved account name")
        return {self.name: "Create"}


@dataclass
class RemoveAccount(Operation):
    TYPE: ClassVar[str] = "Remove Account"
    name: Name

    @property
    def description(self):
        return self.name

    def changes(self, state: LedgerState):  # type:ignore
        return {self.name: "Remove"}


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
    amount: Money
    credit_to: Collection[Name] | None
    debt_from: Collection[Name] | None

    @property
    def description(self):
        return f"({self.amount}) owed by ({'All' if self.debt_from is None else ', '.join(self.debt_from)}), credited to ({'All' if self.credit_to is None else ', '.join(self.credit_to)})"

    def changes(self, accounts: LedgerState) -> ChangeSet:  # type:ignore
        creditors = (
            funcy.lremove("POT", accounts.keys())
            if self.credit_to is None
            else self.credit_to
        )
        debitors = (
            funcy.lremove("POT", accounts.keys())
            if self.debt_from is None
            else self.debt_from
        )
        changes = DefaultDict(lambda: Money("0"))  # type:ignore
        for creditor, balance_change in zip(
            creditors, self.amount.divide_with_no_rest(len(creditors))
        ):
            changes[creditor] += balance_change  # type:ignore
        for debitor, balance_change in zip(
            debitors, self.amount.divide_with_no_rest(len(debitors))
        ):
            changes[debitor] -= balance_change  # type:ignore
        return changes


@dataclass
class SharedExpense(Operation):
    TYPE: ClassVar[str] = "Shared Expense"
    amount: Money
    by: Name
    subject: str

    @property
    def description(self):
        return f"{self.by} has paid {self.amount} for {self.subject}"

    def changes(self, state: LedgerState):
        if state.has_pot:
            return ChangeBalances(
                credit_to=[self.by], debt_from=["POT"], amount=self.amount
            ).changes(state)
        else:
            return ChangeBalances(
                credit_to=[self.by], debt_from=None, amount=self.amount
            ).changes(state)


@dataclass
class Transfer(Operation):
    TYPE: ClassVar[str] = "Money Transfer"
    amount: Money
    by: Name
    to: Name

    @property
    def description(self):
        return f"{self.by} has sent {self.amount} to {self.to}"

    def changes(self, state: LedgerState):
        return ChangeBalances(
            credit_to=[self.by], debt_from=[self.to], amount=self.amount
        ).changes(state)


class AddPot(Operation):
    TYPE: ClassVar[str] = "Add Pot"

    @property
    def description(self):
        return "Add a common pot to the group"

    def changes(self, state: LedgerState):
        if state.has_pot:
            raise RuntimeError("Ledger already has a pot")
        else:
            return {"POT": "Create"}


@dataclass
class Reimburse(Operation):
    TYPE: ClassVar[str] = "Reimburse"
    amount: Money
    to: Name

    @property
    def description(self):
        return f"Reimburse {self.amount} to {self.to} from the pot"

    def changes(self, state: LedgerState):
        if not state.has_pot:
            raise RuntimeError("Reimburse only applies to a ledger with a pot")
        return ChangeBalances(
            amount=self.amount, credit_to=[self.to], debt_from=["POT"]
        ).changes(state)


@dataclass
class RequestContribution(Operation):
    TYPE: ClassVar[str] = "Request Contribution"
    amount: Money

    @property
    def description(self):
        return f"Request contribution of {self.amount} from everyone"

    def changes(self, state: LedgerState):
        if not state.has_pot:
            raise RuntimeError(
                "RequestContribution only applies to a ledger with a pot"
            )
        return ChangeBalances(
            amount=self.amount * (len(state) - 1), credit_to=["POT"], debt_from=None
        ).changes(state)


OPERATION_NAME_TO_CLASS = {
    operation_class.TYPE: operation_class
    for operation_class in [
        AddAccount,
        RemoveAccount,
        ChangeBalances,
        SharedExpense,
        Transfer,
        AddPot,
        Reimburse,
        RequestContribution,
    ]
}


def money_to_float(obj):
    if isinstance(obj, Money):
        return float(obj)
    else:
        return obj


def number_to_money(obj):
    if isinstance(obj, (float, int)):
        return Money(obj)
    else:
        return obj


def operation_as_dict(operation: Operation) -> dict:
    dict_ = {"operation": operation.TYPE} | asdict(operation)
    return funcy.walk_values(money_to_float, dict_)  # type:ignore


def load_operation_from_dict(dict_) -> Operation:
    operation_name = dict_.pop("operation")
    operation_class = OPERATION_NAME_TO_CLASS[operation_name]
    dict_transformed = funcy.walk_values(number_to_money, dict_)
    return operation_class(**dict_transformed)  # type:ignore


# ------------------------ Ledger ------------------------


@dataclass
class LedgerRecord:
    state: LedgerState
    operation: Operation
    changes: ChangeSet


@dataclass
class Ledger:
    records: list[LedgerRecord] = field(default_factory=list)
    LEDGER_FILE = "ledger.yml"

    @property
    def state(self):
        if not self.records:
            return LedgerState()
        else:
            return self.records[-1].state

    # ------------------------ IOs ------------------------

    def save_to_file(self):
        operations_as_dicts = funcy.map(
            operation_as_dict, funcy.pluck_attr("operation", self.records)
        )
        pathlib.Path(self.LEDGER_FILE).write_text(
            yaml.dump_all(
                operations_as_dicts,
                sort_keys=False,
            )
        )

    @classmethod
    def load_from_file(cls) -> Self:
        logger.info(f"load operations from file: {cls.LEDGER_FILE}")
        operation_dicts = yaml.load_all(
            pathlib.Path(cls.LEDGER_FILE).read_text(), Loader=yaml.Loader
        )
        operations = funcy.map(load_operation_from_dict, operation_dicts)
        logger.debug("replay operations")
        ledger = cls()
        for operation in operations:
            ledger.apply(operation)
        logger.debug("ledger loaded")
        return ledger

    @classmethod
    @contextmanager  # type: ignore
    def edit(cls) -> Self:  # type: ignore
        ledger = cls.load_from_file()
        yield ledger  # type: ignore
        ledger.save_to_file()

    # ------------------------ record ------------------------

    def apply(self, operation):
        logger.debug(f"apply operation: {operation}")
        try:
            changes = operation.changes(self.state)
            new_state = self.state.apply_changeset(changes)
        except:
            logger.error("operation could not been applied")
            raise
        self.records.append(
            LedgerRecord(operation=operation, changes=changes, state=new_state)
        )

    # ------------------------ convenience ------------------------

    def _record_operation(self, operation):
        logger.info(f"record operation: {operation}")
        self.apply(operation)

    def add_account(self, name):
        self._record_operation(AddAccount(name))

    def record_shared_expense(self, amount, name, subject):
        self._record_operation(SharedExpense(Money(amount), name, subject))

    def record_transfer(self, amount, by, to):
        self._record_operation(Transfer(Money(amount), by, to))
