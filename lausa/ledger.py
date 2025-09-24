import pathlib
from contextlib import contextmanager
from copy import copy
from dataclasses import dataclass, field
from typing import Self

import funcy
import yaml

from .account import LedgerState
from .io import load_operation_from_dict, operation_as_dict
from .logging import logger
from .money import Money
from .operations import (
    AddAccount,
    AddPot,
    Debt,
    Expenses,
    Operation,
    PaysContribution,
    Reimburse,
    RequestContribution,
    SharedExpense,
    Transfer,
    TransferDebt,
)


@dataclass
class LedgerRecord:
    state: LedgerState
    operation: Operation


@dataclass
class Ledger:
    records: list[LedgerRecord] = field(default_factory=list)
    LEDGER_FILE = "ledger.yml"
    _repr_string = "in-memory"

    def __repr__(self):
        return f"{self.__class__.__name__}(<{self._repr_string!r}>)"

    @property
    def state(self) -> LedgerState:
        if not self.records:
            return LedgerState()
        else:
            return self.records[-1].state

    @property
    def operations(self) -> list[Operation]:
        return [record.operation for record in self.records]

    @property
    def expenses(self) -> Expenses:
        return Expenses(
            funcy.lfilter(funcy.rpartial(isinstance, SharedExpense), self.operations)
        )

    # ------------------------ IOs ------------------------

    def save_to_file(self):
        operations_as_dicts = funcy.map(operation_as_dict, self.operations)
        pathlib.Path(self.LEDGER_FILE).write_text(
            yaml.dump_all(
                operations_as_dicts,
                sort_keys=False,
            )
        )
        self._repr_string = self.LEDGER_FILE

    @classmethod
    def load_from_file(cls) -> Self:
        logger.debug(f"load operations from file: {cls.LEDGER_FILE}")
        operation_dicts = yaml.load_all(
            pathlib.Path(cls.LEDGER_FILE).read_text(), Loader=yaml.Loader
        )
        operations = funcy.map(load_operation_from_dict, operation_dicts)
        logger.debug("replay operations")
        ledger = cls()
        for operation in operations:
            logger.debug(f"apply operation: {operation}")
            ledger.apply(operation)
        logger.debug("ledger loaded")
        ledger._repr_string = ledger.LEDGER_FILE
        return ledger

    @classmethod
    @contextmanager  # type: ignore
    def edit(cls) -> Self:  # type: ignore
        ledger = cls.load_from_file()
        yield ledger  # type: ignore
        ledger.save_to_file()

    # ------------------------ record ------------------------

    def apply(self, operation):
        try:
            new_state = copy(self.state)
            operation.apply_to(new_state)
            new_state.check_equilibrium()
        except:
            logger.error("operation could not been applied")
            raise
        self.records.append(LedgerRecord(operation=operation, state=new_state))

    # ------------------------ convenience ------------------------

    def _record(self, operation):
        logger.debug(f"record operation: {operation}")
        self.apply(operation)

    def add_account(self, name):
        self._record(AddAccount(name))

    def add_pot(self):
        self._record(AddPot())

    def record_debt(self, amount, creditor, debitor, subject):
        self._record(
            Debt(Money(amount), creditor=creditor, debitor=debitor, subject=subject)
        )

    def record_shared_expense(self, amount, name, subject):
        self._record(SharedExpense(Money(amount), name, subject))

    def record_transfer(self, amount, sender, receiver):
        self._record(Transfer(amount=Money(amount), sender=sender, receiver=receiver))

    def record_transfer_debt(self, amount, old_debitor, new_debitor):
        self._record(
            TransferDebt(
                amount=Money(amount), old_debitor=old_debitor, new_debitor=new_debitor
            )
        )

    def request_contribution(self, amount):
        self._record(RequestContribution(Money(amount)))

    def pays_contribution(self, amount, by):
        self._record(PaysContribution(Money(amount), by))

    def reimburse(self, amount, to):
        self._record(Reimburse(Money(amount), to))
