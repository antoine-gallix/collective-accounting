from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import (
    ClassVar,
    Collection,
    DefaultDict,
)

import funcy

from .account import LedgerState, Name
from .money import Money

# -------- account management


@dataclass
class Operation(ABC):
    """An Operation is an action that transforms the ledger state."""

    def __str__(self):
        return f"{self.__class__.__name__}: {self.description}"

    @property
    @abstractmethod
    def description(self) -> str: ...

    @abstractmethod
    def apply_to(self, state: LedgerState) -> None: ...


@dataclass
class AddAccount(Operation):
    name: Name

    @property
    def description(self):
        return self.name

    def apply_to(self, state: LedgerState):
        if self.name == "POT":
            raise ValueError("'POT' is a reserved account name")
        state.add_account(self.name)


@dataclass
class RemoveAccount(Operation):
    name: Name

    @property
    def description(self):
        return self.name

    def apply_to(self, state: LedgerState):
        state.remove_account(self.name)


class AddPot(Operation):
    @property
    def description(self):
        return "Add a common pot to the group"

    def apply_to(self, state: LedgerState):  # type:ignore
        if state.has_pot:
            raise RuntimeError("Ledger already has a pot")
        else:
            state.add_pot()


# -------- debt movements


@dataclass
class SharedExpense(Operation):
    amount: Money
    payer: Name
    subject: str

    @property
    def description(self):
        return f"{self.payer} has paid {self.amount} for {self.subject}"

    def apply_to(self, state: LedgerState):
        state.change_balance(self.payer, amount=-self.amount)
        if state.has_pot:
            state.create_debt(
                amount=self.amount, creditors=[self.payer], debitors=["POT"]
            )
        else:
            state.create_debt(amount=self.amount, creditors=[self.payer], debitors=None)


@dataclass
class TransferDebt(Operation):
    amount: Money
    old_debitor: Name
    new_debitor: Name

    @property
    def description(self):
        return (
            f"{self.new_debitor} covers {self.amount} of debt from {self.old_debitor}"
        )

    def apply_to(self, state: LedgerState):
        state.create_debt(
            creditors=[self.old_debitor],
            debitors=[self.new_debitor],
            amount=self.amount,
        )


@dataclass
class RequestContribution(Operation):
    amount: Money

    @property
    def description(self):
        return f"Request contribution of {self.amount} from everyone"

    def apply_to(self, state: LedgerState):
        if not state.has_pot:
            raise RuntimeError(
                "RequestContribution only applies to a ledger with a pot"
            )
        state.create_debt(
            amount=self.amount * (len(state) - 1), creditors=["POT"], debitors=None
        )


@dataclass
class Transfer(Operation):
    amount: Money
    sender: Name
    receiver: Name

    @property
    def description(self):
        return f"{self.sender} has sent {self.amount} to {self.receiver}"

    def apply_to(self, state: LedgerState):
        state.internal_transfer(
            amount=self.amount, sender=self.sender, receiver=self.receiver
        )


@dataclass
class Reimburse(Operation):
    amount: Money
    receiver: Name

    @property
    def description(self):
        return f"Reimburse {self.amount} to {self.receiver} from the pot"

    def apply_to(self, state: LedgerState):
        if not state.has_pot:
            raise RuntimeError("Reimburse only applies to a ledger with a pot")
        state.internal_transfer(
            amount=self.amount, sender="POT", receiver=self.receiver
        )


@dataclass
class PaysContribution(Operation):
    amount: Money
    sender: Name

    @property
    def description(self):
        return f"{self.sender} contribute {self.amount} to the pot"

    def apply_to(self, state: LedgerState):
        if not state.has_pot:
            raise RuntimeError("PaysContribution only applies to a ledger with a pot")
        state.internal_transfer(amount=self.amount, sender=self.sender, receiver="POT")
