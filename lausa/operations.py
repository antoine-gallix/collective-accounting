from abc import ABC, abstractmethod
from collections import Counter, UserList
from dataclasses import dataclass, field
from typing import Mapping, cast

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

    def has_tag(self, tag):
        return tag in self.tags


class Expenses(UserList[SharedExpense]):
    # -------- selection

    def _filter(self, filter_):
        return self.__class__(funcy.lfilter(filter_, self))

    def select_has_no_tag(self):
        return self._filter(funcy.complement(attrgetter("tags")))

    def select_has_tag(self, tag):
        return self._filter(funcy.rpartial(SharedExpense.has_tag, tag))

    def select_has_all_tags(self, *tags):
        return self._filter(
            funcy.all_fn(*(funcy.rpartial(SharedExpense.has_tag, tag) for tag in tags))
        )

    def select_has_none_of_tags(self, *tags):
        return self._filter(
            funcy.all_fn(
                *(
                    funcy.complement(funcy.rpartial(SharedExpense.has_tag, tag))
                    for tag in tags
                )
            )
        )

    def select_by_id(self, id_: int):
        selection = funcy.select(lambda expense: id(expense) == id_, self)
        selection = cast(list, selection)  # reassure typing
        if len(selection) == 1:
            return selection[0]
        else:
            raise RuntimeError(f"selection returned {len(selection)} matches")

    # -------- tags

    def tags(self) -> list[str]:
        return funcy.lflatten(expense.tags for expense in self)

    def tag_count(self) -> Mapping:
        return Counter(funcy.flatten(expense.tags for expense in self))

    # -------- aggregation

    def sum(self) -> Money:
        return sum(
            funcy.map(attrgetter("amount"), self),
            start=Money(0),
        )


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
