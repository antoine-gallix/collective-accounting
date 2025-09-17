from abc import ABC, abstractmethod
from dataclasses import dataclass

from .account import LedgerState, Name
from .money import Money

# -------- account management


@dataclass
class Operation(ABC):
    """An Operation is an action that transforms the ledger state."""

    @abstractmethod
    def apply_to(self, state: LedgerState) -> None: ...


# -------- account management


@dataclass
class AddAccount(Operation):
    name: Name

    def apply_to(self, state: LedgerState):
        if self.name == "POT":
            raise ValueError("'POT' is a reserved account name")
        state.add_account(self.name)


@dataclass
class RemoveAccount(Operation):
    name: Name

    def apply_to(self, state: LedgerState):
        state.remove_account(self.name)


class AddPot(Operation):
    def apply_to(self, state: LedgerState):  # type:ignore
        if state.has_pot:
            raise RuntimeError("Ledger already has a pot")
        else:
            state.add_pot()


# -------- debt movements


@dataclass
class Debt(Operation):
    amount: Money
    creditor: Name
    debitor: Name
    subject: str

    def apply_to(self, state: LedgerState):
        state.create_debt(
            amount=self.amount, creditors=[self.creditor], debitors=[self.debitor]
        )


@dataclass
class TransferDebt(Operation):
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
class RequestContribution(Operation):
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
class SharedExpense(Operation):
    amount: Money
    payer: Name
    subject: str

    def apply_to(self, state: LedgerState):
        state.change_balance(self.payer, amount=-self.amount)
        if state.has_pot:
            state.create_debt(
                amount=self.amount, creditors=[self.payer], debitors=["POT"]
            )
        else:
            state.create_debt(amount=self.amount, creditors=[self.payer], debitors=None)


@dataclass
class Transfer(Operation):
    amount: Money
    sender: Name
    receiver: Name

    def apply_to(self, state: LedgerState):
        state.internal_transfer(
            amount=self.amount, sender=self.sender, receiver=self.receiver
        )


@dataclass
class Reimburse(Operation):
    amount: Money
    receiver: Name

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

    def apply_to(self, state: LedgerState):
        if not state.has_pot:
            raise RuntimeError("PaysContribution only applies to a ledger with a pot")
        state.internal_transfer(amount=self.amount, sender=self.sender, receiver="POT")
