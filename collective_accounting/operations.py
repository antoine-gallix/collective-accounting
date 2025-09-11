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
