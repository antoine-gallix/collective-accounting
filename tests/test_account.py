from pytest import fixture

from collective_accounting.account import Account
from collective_accounting.money import Money


def test__Account__defaults():
    account = Account()
    assert account == Account(balance=Money(0), diff=Money(0))


@fixture
def account():
    return Account()


def test__Account__expect(account):
    # positive
    account.expect(Money(10))
    assert account == Account(balance=Money(0), diff=Money(10))
    # negative
    account.expect(Money(-30))
    assert account == Account(balance=Money(0), diff=Money(-20))


def test__Account__change_balance(account):
    # positive
    account.change_balance(Money(10))
    assert account == Account(balance=Money(10), diff=Money(-10))
    # negative
    account.change_balance(Money(-40))
    assert account == Account(balance=Money(-30), diff=Money(30))


def test__Account__is_settled(account):
    assert account.is_settled
    account.expect(Money(20))
    assert not account.is_settled
    account.change_balance(Money(20))
    assert account.is_settled
