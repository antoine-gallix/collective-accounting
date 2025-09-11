from pytest import fixture, raises

from collective_accounting.account import Account, LedgerState, PositiveAccount
from collective_accounting.money import Money


@fixture
def account():
    return Account()


@fixture
def ledger_state():
    ledger_state = LedgerState()
    ledger_state.add_account("antoine")
    ledger_state.add_account("baptiste")
    ledger_state.add_account("renan")
    return ledger_state


@fixture
def ledger_state_with_pot(ledger_state):
    ledger_state.add_account("POT")
    return ledger_state


# ------------------------ Account ------------------------


def test__Account__defaults():
    account = Account()
    assert account == Account(balance=Money(0), diff=Money(0))


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


def test__PositiveAccount():
    account = PositiveAccount()
    with raises(RuntimeError):
        account.change_balance(Money(-10))
    assert account == PositiveAccount(balance=Money(0), diff=Money(0))


# ------------------------ LedgerState ------------------------


def test__LedgerState__creation():
    state = LedgerState()
    assert state == {}


# --------


def test__LedgerState__add_account():
    state = LedgerState()
    state.add_account("antoine")
    assert state == {"antoine": Account(balance=Money(0), diff=Money(0))}


def test__LedgerState__add_account__invalid():
    state = LedgerState()
    # not a string
    with raises(TypeError):
        state.add_account(12)  # type: ignore
    # empty string
    with raises(ValueError):
        state.add_account("")


def test__LedgerState__add_account__existing_name(ledger_state):
    with raises(RuntimeError):
        ledger_state.add_account("antoine")


# --------


def test__LedgerState__remove_account(ledger_state):
    ledger_state.remove_account("antoine")
    assert ledger_state == {
        "baptiste": Account(balance=Money(0), diff=Money(0)),
        "renan": Account(balance=Money(0), diff=Money(0)),
    }


def test__LedgerState__remove_account__not_exist(ledger_state):
    with raises(RuntimeError):
        ledger_state.remove_account("kriti")


def test__LedgerState__remove_account__non_null_balance(ledger_state):
    ledger_state.change_balance("antoine", 10)
    with raises(RuntimeError):
        ledger_state.remove_account("antoine")


# --------


def test__LedgerState__change_balance(ledger_state):
    ledger_state.change_balance("antoine", 10)
    assert ledger_state == {
        "antoine": Account(balance=Money(10), diff=Money(-10)),
        "baptiste": Account(balance=Money(0), diff=Money(0)),
        "renan": Account(balance=Money(0), diff=Money(0)),
    }


def test__LedgerState__change_balance__name_do_not_exist(ledger_state):
    with raises(RuntimeError):
        ledger_state.change_balance("kriti", Money(10))


# --------


def test__LedgerState__change_diff(ledger_state):
    ledger_state.change_diff("antoine", 10)
    assert ledger_state == {
        "antoine": Account(balance=Money(0), diff=Money(10)),
        "baptiste": Account(balance=Money(0), diff=Money(0)),
        "renan": Account(balance=Money(0), diff=Money(0)),
    }


def test__LedgerState__change_diff__name_do_not_exist(ledger_state):
    with raises(RuntimeError):
        ledger_state.change_diff("kriti", Money(10))


# --------


def test__LedgerState__check_equilibriumbb(ledger_state):
    ledger_state.check_equilibrium()
    ledger_state.change_diff("antoine", Money(10))
    with raises(RuntimeError):
        ledger_state.check_equilibrium()
    ledger_state.change_diff("renan", Money(-5))
    ledger_state.change_diff("baptiste", Money(-5))
    ledger_state.check_equilibrium()
