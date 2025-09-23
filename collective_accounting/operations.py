from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from operator import attrgetter
from typing import Self

import funcy

from .account import LedgerState, Name
from .money import Money

# -------- account management


@dataclass
class Operation(ABC):
    """An Operation is an action that transforms the ledger state."""

    @abstractmethod
    def apply_to(self, state: LedgerState) -> None: ...


# -------- account management


class AccountOperation(Operation): ...


@dataclass
class AddAccount(AccountOperation):
    name: Name

    def apply_to(self, state: LedgerState):
        if self.name == "POT":
            raise ValueError("'POT' is a reserved account name")
        state.add_account(self.name)


@dataclass
class RemoveAccount(AccountOperation):
    name: Name

    def apply_to(self, state: LedgerState):
        state.remove_account(self.name)


class AddPot(AccountOperation):
    def apply_to(self, state: LedgerState):  # type:ignore
        if state.has_pot:
            raise RuntimeError("Ledger already has a pot")
        else:
            state.add_pot()


# -------- debt movements


class AccountingOperation(Operation): ...


@dataclass
class Debt(AccountingOperation):
    amount: Money
    creditor: Name
    debitor: Name
    subject: str

    def apply_to(self, state: LedgerState):
        state.create_debt(
            amount=self.amount, creditors=[self.creditor], debitors=[self.debitor]
        )


@dataclass
class TransferDebt(AccountingOperation):
    amount: Money
    old_debitor: Name
    new_debitor: Name

    def apply_to(self, state: LedgerState):
        state.create_debt(
            creditors=[self.old_debitor],
            debitors=[self.new_debitor],
            amount=self.amount,
        )


@dataclass
class RequestContribution(AccountingOperation):
    amount: Money

    def apply_to(self, state: LedgerState):
        if not state.has_pot:
            raise RuntimeError(
                "RequestContribution only applies to a ledger with a pot"
            )
        state.create_debt(
            amount=self.amount * (len(state) - 1), creditors=["POT"], debitors=None
        )


# -------- money movements


@dataclass
class SharedExpense(AccountingOperation):
    amount: Money
    payer: Name
    subject: str
    tags: tuple = field(default_factory=tuple)

    def apply_to(self, state: LedgerState):
        state.change_balance(self.payer, amount=-self.amount)
        if state.has_pot:
            state.create_debt(
                amount=self.amount, creditors=[self.payer], debitors=["POT"]
            )
        else:
            state.create_debt(amount=self.amount, creditors=[self.payer], debitors=None)


def sum_expenses(expenses: list[SharedExpense]) -> Money:
    return sum(
        funcy.map(attrgetter("amount"), expenses),
        start=Money(0),
    )


def filter_expenses(expenses: list[SharedExpense], tag: str) -> list[SharedExpense]:
    return funcy.lfilter(lambda o: tag in o.tags, expenses)


@dataclass
class Transfer(AccountingOperation):
    amount: Money
    sender: Name
    receiver: Name

    def apply_to(self, state: LedgerState):
        state.internal_transfer(
            amount=self.amount, sender=self.sender, receiver=self.receiver
        )


@dataclass
class Reimburse(AccountingOperation):
    amount: Money
    receiver: Name

    def apply_to(self, state: LedgerState):
        if not state.has_pot:
            raise RuntimeError("Reimburse only applies to a ledger with a pot")
        state.internal_transfer(
            amount=self.amount, sender="POT", receiver=self.receiver
        )


@dataclass
class PaysContribution(AccountingOperation):
    amount: Money
    sender: Name

    def apply_to(self, state: LedgerState):
        if not state.has_pot:
            raise RuntimeError("PaysContribution only applies to a ledger with a pot")
        state.internal_transfer(amount=self.amount, sender=self.sender, receiver="POT")
