from dataclasses import dataclass
from typing import Collection

import funcy

from .logging import logger
from .money import Money


@dataclass
class Account:
    """An Account represents current and future money of a user in the ledger"""

    # current amount of money in the account
    balance: Money = Money(0)
    # difference to the target state
    diff: Money = Money(0)

    @property
    def is_settled(self):
        return self.diff == Money(0)

    def expect(self, amount: Money):
        self.diff += amount

    def change_balance(self, amount: Money):
        self.balance += amount
        self.diff -= amount


class PositiveAccount(Account):
    """An account whose balance cannot get negative"""

    def change_balance(self, amount: Money):
        if -amount > self.balance:
            raise RuntimeError("account balance cannot be negative")
        super().change_balance(amount)


type Name = str


class LedgerState(dict[Name, Account]):
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

    @classmethod
    def _validate_name(cls, name):
        if not isinstance(name, str):
            raise TypeError("name is not a string")
        if not name:
            raise ValueError("name string is empty")

    def add_account(self, name: str):
        self._validate_name(name)
        if name in self:
            raise RuntimeError("account already exists")
        self[name] = Account()

    def remove_account(self, name: str):
        try:
            if not self[name].is_settled:
                raise RuntimeError("account cannot be removed if not settled")
            del self[name]
        except KeyError:
            raise RuntimeError("account does not exists")

    def change_balance(self, name: str, amount: Money):
        logger.debug(f"balance change: {name} {amount!s}")
        try:
            self[name].change_balance(amount)
        except KeyError:
            raise RuntimeError("account does not exists")

    def change_diff(self, name: str, amount: Money):
        logger.debug(f"difference change: {name} {amount!s}")
        try:
            self[name].expect(amount)
        except KeyError:
            raise RuntimeError("account does not exists")

    def check_equilibrium(self):
        if (error := sum(account.diff for account in self.values())) != 0:
            raise RuntimeError(f"accounts not equilibrated. Sum of diffs is {error:+}")

    def create_debt(
        self,
        amount: Money,
        creditors: Collection[Name] | None,
        debitors: Collection[Name] | None,
    ):
        """Generic Balance Change Operation

        Represents the transfer of credit from one group of accounts to another group of accounts. The amount of the change is divided between the creditors, and added to their balance; between the debitors, it is divided and substracted from their balance.

        Specifying None for either group is interpreted as `all accounts`

        More precisely:
            individual_creditor_balance_change = amount / len(add_to)
            individual_debitor_balance_change = - amount / len(substract_from)"""
        creditors = (
            funcy.lremove("POT", self.keys()) if creditors is None else creditors
        )
        debitors = funcy.lremove("POT", self.keys()) if debitors is None else debitors
        for creditor, balance_change in zip(
            creditors, amount.divide_with_no_rest(len(creditors))
        ):
            self[creditor].diff += balance_change  # type:ignore
        for debitor, balance_change in zip(
            debitors, amount.divide_with_no_rest(len(debitors))
        ):
            self[debitor].diff -= balance_change  # type:ignore
