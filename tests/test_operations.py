from pytest import fixture, raises

from collective_accounting.account import Account, LedgerState, PositiveAccount
from collective_accounting.money import Money
from collective_accounting.operations import (
    AddAccount,
    AddPot,
    Debt,
    PaysContribution,
    Reimburse,
    RemoveAccount,
    RequestContribution,
    SharedExpense,
    Transfer,
    TransferDebt,
)


@fixture
def new_state():
    return LedgerState()


@fixture
def state(new_state):
    new_state.add_account("antoine")
    new_state.add_account("baptiste")
    new_state.add_account("renan")
    return new_state


@fixture
def state_with_pot(state):
    state.add_pot()
    return state


# -------- account management


def test__AddAccount(new_state):
    operation = AddAccount("antoine")
    operation.apply_to(new_state)
    assert list(new_state.keys()) == ["antoine"]


def test__AddAccount__pot_name_reserved(new_state):
    operation = AddAccount("POT")
    with raises(ValueError):
        operation.apply_to(new_state)


def test__RemoveAccount(state):
    operation = RemoveAccount("antoine")
    operation.apply_to(state)
    assert list(state.keys()) == ["baptiste", "renan"]


def test__CreatePot(state):
    operation = AddPot()
    operation.apply_to(state)
    assert state == {
        "POT": PositiveAccount(balance=Money("0.00"), diff=Money("0.00")),
        "antoine": Account(balance=Money("0.00"), diff=Money("0.00")),
        "baptiste": Account(balance=Money("0.00"), diff=Money("0.00")),
        "renan": Account(balance=Money("0.00"), diff=Money("0.00")),
    }
    assert state.has_pot


def test__CreatePot__already_exist(state):
    operation = AddPot()
    operation.apply_to(state)
    with raises(RuntimeError):
        operation.apply_to(state)


# -------- debt movement


def test__Operation__debt(state):
    operation = Debt(
        amount=Money(10), debitor="renan", creditor="antoine", subject="lunch"
    )
    operation.apply_to(state)
    assert state == {
        "antoine": Account(balance=Money("0.00"), diff=Money("10.00")),
        "baptiste": Account(balance=Money("0.00"), diff=Money("0.00")),
        "renan": Account(balance=Money("0.00"), diff=Money("-10.00")),
    }


def test__TransferDebt(state):
    operation = TransferDebt(
        amount=Money(100), old_debitor="baptiste", new_debitor="renan"
    )
    operation.apply_to(state)
    assert state == {
        "antoine": Account(balance=Money("0.00"), diff=Money("0.00")),
        "baptiste": Account(balance=Money("0.00"), diff=Money("100.00")),
        "renan": Account(balance=Money("0.00"), diff=Money("-100.00")),
    }


def test__RequestContribution(state_with_pot):
    operation = RequestContribution(Money(100))
    operation.apply_to(state_with_pot)
    assert state_with_pot == {
        "antoine": Account(balance=Money("0.00"), diff=Money("-100.00")),
        "baptiste": Account(balance=Money("0.00"), diff=Money("-100.00")),
        "renan": Account(balance=Money("0.00"), diff=Money("-100.00")),
        "POT": PositiveAccount(balance=Money("0.00"), diff=Money("300.00")),
    }


def test__operation__RequestContribution__no_pot(state):
    operation = RequestContribution(Money(100))
    with raises(RuntimeError):
        assert operation.apply_to(state)


# -------- money movement


def test__SharedExpense(state):
    operation = SharedExpense(
        amount=Money(100), payer="antoine", subject="renting a van"
    )
    operation.apply_to(state)
    assert state == {
        "antoine": Account(balance=Money("-100.00"), diff=Money("66.66")),
        "baptiste": Account(balance=Money("0.00"), diff=Money("-33.33")),
        "renan": Account(balance=Money("0.00"), diff=Money("-33.33")),
    }


def test__SharedExpense_with_pot(state_with_pot):
    operation = SharedExpense(
        amount=Money(100), payer="antoine", subject="renting a van"
    )
    operation.apply_to(state_with_pot)
    assert state_with_pot == {
        "antoine": Account(balance=Money("-100.00"), diff=Money("100.00")),
        "POT": PositiveAccount(balance=Money("0.00"), diff=Money("-100.00")),
        "baptiste": Account(balance=Money("0.00"), diff=Money("0.00")),
        "renan": Account(balance=Money("0.00"), diff=Money("0.00")),
    }


def test__SharedExpense__tags():
    no_tag = SharedExpense(
        amount=Money(100), payer="antoine", subject="bribe authorities"
    )
    assert no_tag.tags == ()
    one_tag = SharedExpense(
        amount=Money(100), payer="antoine", subject="renting a van", tags=("transport",)
    )
    assert one_tag.tags == ("transport",)
    one_tag = SharedExpense(
        amount=Money(200),
        payer="antoine",
        subject="kitchen tent",
        tags=("asset", "kitchen"),
    )
    assert one_tag.tags == ("asset", "kitchen")


def test__Transfer(state):
    operation = Transfer(amount=Money(100), sender="baptiste", receiver="antoine")
    operation.apply_to(state)
    assert state == {
        "antoine": Account(balance=Money("100.00"), diff=Money("-100.00")),
        "baptiste": Account(balance=Money("-100.00"), diff=Money("100.00")),
        "renan": Account(balance=Money("0.00"), diff=Money("0.00")),
    }


def test__operation__Reimburse(state_with_pot):
    state_with_pot.change_balance("POT", Money("100"))
    operation = Reimburse(Money(50), "antoine")
    operation.apply_to(state_with_pot)
    assert state_with_pot == {
        "antoine": Account(balance=Money("50.00"), diff=Money("-50.00")),
        "baptiste": Account(balance=Money("0.00"), diff=Money("0.00")),
        "renan": Account(balance=Money("0.00"), diff=Money("0.00")),
        "POT": PositiveAccount(balance=Money("50.00"), diff=Money("50.00")),
    }


def test__operation__Reimburse__no_pot(state):
    operation = Reimburse(Money(50), "Antoine")
    with raises(RuntimeError):
        assert operation.apply_to(state)


def test__operation__PaysContribution(state_with_pot):
    operation = PaysContribution(amount=Money(100), sender="antoine")
    operation.apply_to(state_with_pot)
    assert state_with_pot == {
        "antoine": Account(balance=Money("-100.00"), diff=Money("100.00")),
        "baptiste": Account(balance=Money("0.00"), diff=Money("0.00")),
        "renan": Account(balance=Money("0.00"), diff=Money("0.00")),
        "POT": PositiveAccount(balance=Money("100.00"), diff=Money("-100.00")),
    }


def test__operation__PaysContribution__no_pot(state):
    operation = PaysContribution(amount=Money(100), sender="antoine")
    with raises(RuntimeError):
        assert operation.apply_to(state)
