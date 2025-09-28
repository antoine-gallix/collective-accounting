from abc import ABC, abstractmethod
from collections import Counter, UserList
from dataclasses import dataclass, field
from operator import attrgetter
from typing import Collection, Iterable, Mapping, Self

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


class Expenses(UserList[SharedExpense]):
    def sum(self) -> Money:
        return sum(
            funcy.map(attrgetter("amount"), self),
            start=Money(0),
        )

    def filter(self, has_tag: str | None | Collection[str], negate=False) -> Self:
        """Select a subset of expenses

        has_tags:
            string: select expenses with given tag
            list or tuple: select expenses all tags in the collection
        """
        match has_tag:
            case None:

                def pred(o: SharedExpense) -> bool:
                    return len(o.tags) == 0

            case str(tag):

                def pred(o: SharedExpense) -> bool:
                    return tag in o.tags
            case tuple(tags) | list(tags):

                def pred(o: SharedExpense) -> bool:
                    return all((tag in o.tags) for tag in tags)

        if negate:
            pred = funcy.complement(pred)  # type:ignore
        return self.__class__(funcy.lfilter(pred, self))

    def tags(self, unique=True) -> list[str]:
        tags = funcy.flatten(expense.tags for expense in self)
        return list(set(tags)) if unique else list(tags)

    def tag_count(self) -> Mapping:
        return Counter(self.tags(unique=False))


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
