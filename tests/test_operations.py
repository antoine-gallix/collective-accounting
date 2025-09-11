from pytest import fixture, raises

from collective_accounting.account import LedgerState
from collective_accounting.operations import AddAccount, RemoveAccount


@fixture
def new_state():
    return LedgerState()


@fixture
def state(new_state):
    new_state.add_account("antoine")
    new_state.add_account("baptiste")
    new_state.add_account("renan")
    return new_state


def test__AddAccount(new_state):
    operation = AddAccount("antoine")
    assert str(operation) == "AddAccount: antoine"
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
