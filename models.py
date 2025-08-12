from dataclasses import dataclass, field
from loguru import logger
import funcy


@dataclass
class Account:
    name: str
    credit: float = 0

    def change_credit(self, change: int | float):
        logger.info(f"applying {change:+.2f} credit change to account {self.name!r}")
        self.credit += change


@dataclass
class Group:
    accounts: list[Account] = field(default_factory=list)

    def add_account(self, name):
        logger.info(f"creating new account: {name!r}")
        account = Account(name)
        self.accounts.append(account)
        return account

    def add_shared_credit(self, name, value):
        logger.info(f"creating new account: {name!r}")
        credited_account, debited_accounts = funcy.split(
            lambda account: account.name == name, self.accounts
        )
        if not (splits := len(debited_accounts)):
            logger.warning("no other account to share with")
            return
        debt_share = -value / splits
        credited_account.change_credit(value - debt_share)
        for debited_account in debited_accounts:
            debited_account.change_credit(debt_share)
