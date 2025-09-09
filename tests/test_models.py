import pathlib
from textwrap import dedent

from pytest import fixture, raises

from collective_accounting.models import (
    AddAccount,
    AddPot,
    ChangeBalances,
    Ledger,
    LedgerState,
    Money,
    PaysContribution,
    Reimburse,
    RemoveAccount,
    RequestContribution,
    SharedExpense,
    Transfer,
)

# ------------------------ fixtures ------------------------


@fixture
def ledger_state():
    state = LedgerState()
    state._add_account("antoine")
    state._add_account("baptiste")
    state._add_account("renan")
    return state


@fixture
def ledger_state_with_pot(ledger_state):
    ledger_state._add_account("POT")
    return ledger_state


# ------------------------ accounts ------------------------


def test__LedgerState__creation():
    state = LedgerState()
    assert state == {}


def test__LedgerState__add_account():
    state = LedgerState()
    state._add_account("antoine")
    assert state == {"antoine": 0}


def test__LedgerState__add_account__invalid():
    state = LedgerState()
    # not a string
    with raises(TypeError):
        state._add_account(12)  # type: ignore
    # empty string
    with raises(ValueError):
        state._add_account("")


def test__LedgerState__add_account__existing_name(ledger_state):
    with raises(RuntimeError):
        ledger_state._add_account("antoine")


def test__LedgerState__remove_account(ledger_state):
    ledger_state._remove_account("antoine")
    assert ledger_state == {"baptiste": 0, "renan": 0}


def test__LedgerState__remove_account__not_exist(ledger_state):
    with raises(RuntimeError):
        ledger_state._remove_account("kriti")


def test__LedgerState__remove_account__non_null_balance(ledger_state):
    ledger_state._change_balance("antoine", 10)
    with raises(RuntimeError):
        ledger_state._remove_account("antoine")


def test__LedgerState__change_balance(ledger_state):
    assert ledger_state == {
        "antoine": 0,
        "baptiste": 0,
        "renan": 0,
    }
    ledger_state._change_balance("antoine", 10)
    assert ledger_state == {
        "antoine": 10,
        "baptiste": 0,
        "renan": 0,
    }


def test__LedgerState__change_balance__name_do_not_exist():
    state = LedgerState()
    state._add_account("antoine")
    with raises(RuntimeError):
        state._change_balance("baptiste", Money(10))


def test__LedgerState__check_balances(ledger_state):
    ledger_state._check_balances()
    ledger_state._change_balance("antoine", Money(10))
    with raises(RuntimeError):
        ledger_state._check_balances()
    ledger_state._change_balance("renan", Money(-5))
    ledger_state._change_balance("baptiste", Money(-5))
    ledger_state._check_balances()


# ------------------------ operations ------------------------


def test__operations__AddAccount(ledger_state):
    operation = AddAccount("kriti")
    assert operation.TYPE == "Add Account"
    assert operation.description == "kriti"
    assert operation.changes(ledger_state) == {"kriti": "Create"}


def test__operations__RemoveAccount(ledger_state):
    operation = RemoveAccount("kriti")
    assert operation.TYPE == "Remove Account"
    assert operation.description == "kriti"
    assert operation.changes(ledger_state) == {"kriti": "Remove"}


def test__operations__AddPot(ledger_state):
    operation = AddPot()
    assert operation.TYPE == "Add Pot"
    assert operation.description == "Add a common pot to the group"
    assert operation.changes(ledger_state) == {"POT": "Create"}


def test__operations__ChangeBalances__one_to_one(ledger_state):
    operation = ChangeBalances(
        amount=Money(10), add_to=["antoine"], deduce_from=["baptiste"]
    )
    assert operation.TYPE == "Change Balances"
    assert operation.description == "(10.00) owed by (baptiste), credited to (antoine)"
    assert operation.changes(ledger_state) == {
        "antoine": Money(10),
        "baptiste": Money(-10),
    }


def test__operations__ChangeBalances__one_to_two(ledger_state):
    operation = ChangeBalances(
        amount=Money(10), add_to=["antoine", "renan"], deduce_from=["baptiste"]
    )
    assert (
        operation.description
        == "(10.00) owed by (baptiste), credited to (antoine, renan)"
    )
    assert operation.changes(ledger_state) == {
        "antoine": Money(5),
        "renan": Money(5),
        "baptiste": Money(-10),
    }


def test__operations__ChangeBalances__one_to_all(ledger_state):
    operation = ChangeBalances(amount=Money(10), add_to=None, deduce_from=["baptiste"])
    assert operation.description == "(10.00) owed by (baptiste), credited to (All)"
    assert operation.changes(ledger_state) == {
        "antoine": Money("3.34"),
        "renan": Money("3.33"),
        "baptiste": Money("-6.67"),
    }


def test__operations__ChangeBalances__two_to_one(ledger_state):
    operation = ChangeBalances(
        amount=Money(10), add_to=["renan"], deduce_from=["baptiste", "antoine"]
    )
    assert (
        operation.description
        == "(10.00) owed by (baptiste, antoine), credited to (renan)"
    )
    assert operation.changes(ledger_state) == {
        "renan": Money("10"),
        "baptiste": Money("-5"),
        "antoine": Money("-5"),
    }


def test__operations__ChangeBalances__two_to_two(ledger_state):
    operation = ChangeBalances(
        amount=Money(10),
        add_to=["renan", "baptiste"],
        deduce_from=["baptiste", "antoine"],
    )
    assert (
        operation.description
        == "(10.00) owed by (baptiste, antoine), credited to (renan, baptiste)"
    )
    assert operation.changes(ledger_state) == {
        "renan": Money("5"),
        "baptiste": Money("0"),
        "antoine": Money("-5"),
    }


def test__operations__ChangeBalances__two_to_all(ledger_state):
    operation = ChangeBalances(
        amount=Money(10), add_to=None, deduce_from=["baptiste", "antoine"]
    )
    assert (
        operation.description
        == "(10.00) owed by (baptiste, antoine), credited to (All)"
    )
    assert operation.changes(ledger_state) == {
        "antoine": Money("-1.66"),
        "renan": Money("3.33"),
        "baptiste": Money("-1.67"),
    }


def test__operations__ChangeBalances__all_to_one(ledger_state):
    operation = ChangeBalances(amount=Money(10), add_to=["antoine"], deduce_from=None)
    assert operation.description == "(10.00) owed by (All), credited to (antoine)"
    assert operation.changes(ledger_state) == {
        "antoine": Money("6.66"),
        "baptiste": Money("-3.33"),
        "renan": Money("-3.33"),
    }


def test__operations__ChangeBalances__all_to_two(ledger_state):
    operation = ChangeBalances(
        amount=Money(10), add_to=["antoine", "baptiste"], deduce_from=None
    )
    assert (
        operation.description
        == "(10.00) owed by (All), credited to (antoine, baptiste)"
    )
    assert operation.changes(ledger_state) == {
        "antoine": Money("1.66"),
        "baptiste": Money("1.67"),
        "renan": Money("-3.33"),
    }


def test__operations__ChangeBalances__all_to_all(ledger_state):
    operation = ChangeBalances(amount=Money(10), add_to=None, deduce_from=None)
    assert operation.description == "(10.00) owed by (All), credited to (All)"
    assert operation.changes(ledger_state) == {
        "antoine": Money("0"),
        "baptiste": Money("0"),
        "renan": Money("0"),
    }


def test__operations__SharedExpense(ledger_state):
    operation = SharedExpense(amount=Money(100), by="antoine", subject="renting a van")
    assert operation.description == "antoine has paid 100.00 for renting a van"
    assert operation.changes(ledger_state) == {
        "antoine": Money("66.66"),
        "baptiste": Money("-33.33"),
        "renan": Money("-33.33"),
    }


def test__operation__SharedExpense_with_pot(ledger_state_with_pot):
    operation = SharedExpense(amount=Money(100), by="antoine", subject="renting a van")
    assert operation.description == "antoine has paid 100.00 for renting a van"
    assert operation.changes(ledger_state_with_pot) == {
        "antoine": Money("100.00"),
        "POT": Money("-100.00"),
    }


def test__operations__Transfer(ledger_state):
    operation = Transfer(amount=Money(100), by="baptiste", to="antoine")
    assert operation.description == "baptiste has sent 100.00 to antoine"
    assert operation.changes(ledger_state) == {
        "antoine": Money("-100"),
        "baptiste": Money("100"),
    }


def test__operation__CreatePot(ledger_state):
    operation = AddPot()
    assert operation.description == "Add a common pot to the group"
    assert operation.changes(ledger_state) == {
        "POT": "Create",
    }


def test__operation__CreatePot__reserved_name(ledger_state):
    operation = AddAccount("POT")
    with raises(ValueError):
        assert operation.changes(ledger_state)


def test__operation__Reimburse(ledger_state_with_pot):
    operation = Reimburse(Money(50), "Antoine")
    assert operation.description == "Reimburse 50.00 to Antoine from the pot"
    assert operation.changes(ledger_state_with_pot) == {
        "Antoine": Money("50.00"),
        "POT": Money("-50.00"),
    }


def test__operation__Reimburse__no_pot(ledger_state):
    operation = Reimburse(Money(50), "Antoine")
    with raises(RuntimeError):
        assert operation.changes(ledger_state)


def test__operation__RequestContribution(ledger_state_with_pot):
    operation = RequestContribution(Money(100))
    assert operation.description == "Request contribution of 100.00 from everyone"
    assert operation.changes(ledger_state_with_pot) == {
        "antoine": Money("-100.00"),
        "baptiste": Money("-100.00"),
        "renan": Money("-100.00"),
        "POT": Money("300.00"),
    }


def test__operation__RequestContribution__no_pot(ledger_state):
    operation = RequestContribution(Money(100))
    with raises(RuntimeError):
        assert operation.changes(ledger_state)


def test__operation__PaysContribution(ledger_state_with_pot):
    operation = PaysContribution(amount=Money(100), by="antoine")
    assert operation.description == "antoine contribute 100.00 to the pot"
    assert operation.changes(ledger_state_with_pot) == {
        "antoine": Money("+100.00"),
        "POT": Money("-100.00"),
    }


def test__operation__PaysContribution__no_pot(ledger_state):
    operation = PaysContribution(amount=Money(100), by="antoine")
    with raises(RuntimeError):
        assert operation.changes(ledger_state)


# ------------------------ ledger ------------------------


@fixture
def ledger():
    ledger = Ledger()
    ledger.apply(AddAccount("antoine"))
    ledger.apply(AddAccount("baptiste"))
    ledger.apply(AddAccount("renan"))
    return ledger


@fixture
def ledger_with_pot(ledger):
    ledger.apply(AddPot())
    return ledger


# --------


def test__Ledger__create():
    ledger = Ledger()
    assert ledger.state == {}


# -------- account operations


def test__Ledger__add_account(ledger):
    ledger.apply(AddAccount("kriti"))
    assert list(ledger.state.keys()) == ["antoine", "baptiste", "renan", "kriti"]


def test__Ledger__add_account__invalid(ledger):
    with raises(TypeError):
        ledger.apply(AddAccount(123))  # type:ignore
    with raises(ValueError):
        ledger.apply(AddAccount(""))


def test__Ledger__add_account__reserved(ledger):
    with raises(ValueError):
        ledger.apply(AddAccount("POT"))


def test__Ledger__add_account__already_exists(ledger):
    with raises(RuntimeError):
        ledger.apply(AddAccount("antoine"))


def test__Ledger__remove_account(ledger):
    ledger.apply(RemoveAccount("antoine"))
    assert list(ledger.state.keys()) == ["baptiste", "renan"]


def test__Ledger__remove_account__error(ledger):
    with raises(RuntimeError):
        ledger.apply(RemoveAccount("kriti"))
    ledger.apply(Transfer(by="antoine", to="renan", amount=Money(10)))
    with raises(RuntimeError):
        ledger.apply(RemoveAccount("antoine"))


def test__Ledger__add_pot(ledger):
    ledger.apply(AddPot())
    assert list(ledger.state.keys()) == ["antoine", "baptiste", "renan", "POT"]
    assert ledger.pot == Money(0)


# -------- balance operations


def test__Ledger__change_balance(ledger):
    ledger.apply(
        ChangeBalances(add_to=None, deduce_from=["antoine", "renan"], amount=Money(100))
    )
    assert ledger.state == {
        "antoine": Money("-16.66"),
        "baptiste": Money("33.33"),
        "renan": Money("-16.67"),
    }


def test__Ledger__shared_expense(ledger):
    ledger.apply(SharedExpense(by="antoine", amount=Money(100), subject="buy wood"))
    assert ledger.state == {
        "antoine": Money("66.66"),
        "baptiste": Money("-33.33"),
        "renan": Money("-33.33"),
    }


def test__Ledger__transfer(ledger):
    ledger.apply(Transfer(by="antoine", to="renan", amount=Money(50)))
    assert ledger.state == {
        "antoine": Money("50"),
        "baptiste": Money("0"),
        "renan": Money("-50"),
    }


def test__Ledger_w_pot__contribution(ledger_with_pot):
    assert ledger_with_pot.state["POT"] == 0
    assert ledger_with_pot.pot == 0
    ledger_with_pot.apply(RequestContribution(Money(100)))
    assert ledger_with_pot.state["POT"] == 300
    assert ledger_with_pot.pot == 0
    ledger_with_pot.apply(PaysContribution(Money(100), "baptiste"))
    assert ledger_with_pot.state["POT"] == 200
    assert ledger_with_pot.pot == 100


def test__Ledger_w_pot__reimburse(ledger_with_pot):
    ledger_with_pot.state["POT"] = Money(-100)
    ledger_with_pot.state["Antoine"] = Money(100)
    ledger_with_pot.pot = 300
    ledger_with_pot.apply(Reimburse(Money(100), "antoine"))
    assert ledger_with_pot.state["POT"] == Money(0)
    assert ledger_with_pot.state["Antoine"] == Money(0)
    assert ledger_with_pot.pot == 200


# ------------------------ IOs ------------------------


@fixture
def tmp_ledger_file(mocker, tmp_path):
    mocker.patch.object(Ledger, "LEDGER_FILE", tmp_path / Ledger.LEDGER_FILE)


@fixture
def ledger_with_operations(ledger):
    for operation in [
        AddAccount("kriti"),
        ChangeBalances(
            amount=Money(50), add_to=["antoine"], deduce_from=["renan", "baptiste"]
        ),
        SharedExpense(by="baptiste", amount=Money(40), subject="buy lots of coffee"),
        Transfer(by="antoine", to="baptiste", amount=Money(12)),
    ]:
        ledger.apply(operation)
    return ledger


def test__Ledger__save_to_file(ledger_with_operations, tmp_ledger_file):
    ledger_with_operations.save_to_file()
    # ---
    file_content = pathlib.Path(ledger_with_operations.LEDGER_FILE).read_text()
    assert file_content == dedent("""\
            operation: Add Account
            name: antoine
            ---
            operation: Add Account
            name: baptiste
            ---
            operation: Add Account
            name: renan
            ---
            operation: Add Account
            name: kriti
            ---
            operation: Change Balances
            amount: 50.0
            add_to:
            - antoine
            deduce_from:
            - renan
            - baptiste
            ---
            operation: Shared Expense
            amount: 40.0
            by: baptiste
            subject: buy lots of coffee
            ---
            operation: Money Transfer
            amount: 12.0
            by: antoine
            to: baptiste
            """)


def test__Ledger__load_from_file(ledger_with_operations, tmp_ledger_file):
    ledger_with_operations.save_to_file()
    ledger_loaded = Ledger.load_from_file()
    assert ledger_loaded.state == ledger_with_operations.state
