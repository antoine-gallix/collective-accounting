from dataclasses import dataclass

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
