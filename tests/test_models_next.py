from decimal import Decimal

from pytest import fixture, raises

from collective_accounting.models_next import (
    AccountCreation,
    AccountRemoval,
    AddAccount,
    BalanceChange,
    ChangeBalances,
    Ledger,
    LedgerState,
    RemoveAccount,
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
        state._change_balance("baptiste", 10)


def test__LedgerState__check_balances(ledger_state):
    ledger_state._check_balances()
    ledger_state._change_balance("antoine", 10)
    with raises(RuntimeError):
        ledger_state._check_balances()
    ledger_state._change_balance("renan", -5)
    ledger_state._change_balance("baptiste", -5)
    ledger_state._check_balances()


# ------------------------ accounts and changes ------------------------


def test__LedgerState__apply_change__AccountCreation(ledger_state):
    ledger_state.apply_change(AccountCreation(name="kriti"))
    assert ledger_state == {
        "antoine": Decimal("0"),
        "baptiste": Decimal("0"),
        "kriti": Decimal("0"),
        "renan": Decimal("0"),
    }
    with raises(RuntimeError):
        ledger_state.apply_change(AccountCreation(name="kriti"))


def test__LedgerState__apply_change__AccountRemoval(ledger_state):
    ledger_state.apply_change(AccountRemoval(name="antoine"))
    assert ledger_state == {
        "baptiste": Decimal("0"),
        "renan": Decimal("0"),
    }
    with raises(RuntimeError):
        ledger_state.apply_change(AccountRemoval(name="finn"))
    ledger_state._change_balance("baptiste", 12)
    with raises(RuntimeError):
        ledger_state.apply_change(AccountRemoval(name="baptiste"))


def test__LedgerState__apply_change__BalanceChange(ledger_state):
    ledger_state.apply_change(BalanceChange(name="antoine", amount=12))
    assert ledger_state == {
        "antoine": Decimal(12),
        "baptiste": Decimal("0"),
        "renan": Decimal("0"),
    }


def test__LedgerState__apply_changeset__AccountCreation(ledger_state):
    new_state = ledger_state.apply_changeset([AccountCreation(name="finn")])
    assert new_state == {
        "antoine": Decimal("0"),
        "baptiste": Decimal("0"),
        "renan": Decimal("0"),
        "finn": Decimal("0"),
    }
    with raises(RuntimeError):
        ledger_state.apply_changeset([AccountCreation(name="antoine")])


def test__LedgerState__apply_changeset__AccountRemoval(ledger_state):
    new_state = ledger_state.apply_changeset([AccountRemoval(name="antoine")])
    assert new_state == {
        "baptiste": Decimal("0"),
        "renan": Decimal("0"),
    }
    with raises(RuntimeError):
        ledger_state.apply_changeset([AccountRemoval(name="finn")])


def test__LedgerState__apply_changeset__BalanceChange(ledger_state):
    new_state = ledger_state.apply_changeset(
        [
            BalanceChange(name="antoine", amount=10),
            BalanceChange(name="renan", amount=-5),
            BalanceChange(name="baptiste", amount=-5),
        ]
    )
    assert new_state == {
        "antoine": Decimal("10"),
        "baptiste": Decimal("-5"),
        "renan": Decimal("-5"),
    }
    with raises(RuntimeError):
        ledger_state.apply_changeset(
            [
                BalanceChange(name="antoine", amount=10),
                BalanceChange(name="renan", amount=-5),
            ]
        )


# ------------------------ operations ------------------------


def test__operations__AddAccount(ledger_state):
    operation = AddAccount("kriti")
    assert operation.TYPE == "Add Account"
    assert operation.description == "kriti"
    assert operation.changes(ledger_state) == [AccountCreation("kriti")]


def test__operations__RemoveAccount(ledger_state):
    operation = RemoveAccount("kriti")
    assert operation.TYPE == "Remove Account"
    assert operation.description == "kriti"
    assert operation.changes(ledger_state) == [AccountRemoval("kriti")]


def test__operations__ChangeBalances__one_to_one(ledger_state):
    operation = ChangeBalances(amount=10, credit_to=["antoine"], debt_from=["baptiste"])
    assert operation.TYPE == "Change Balances"
    assert (
        operation.description == "transfering credit (10) from (baptiste) to (antoine)"
    )
    assert operation.changes(ledger_state) == [
        BalanceChange("antoine", Decimal(10)),
        BalanceChange("baptiste", Decimal(-10)),
    ]


def test__operations__ChangeBalances__one_to_two(ledger_state):
    operation = ChangeBalances(
        amount=10, credit_to=["antoine", "renan"], debt_from=["baptiste"]
    )
    assert (
        operation.description
        == "transfering credit (10) from (baptiste) to (antoine, renan)"
    )
    assert operation.changes(ledger_state) == [
        BalanceChange("antoine", Decimal(5)),
        BalanceChange("renan", Decimal(5)),
        BalanceChange("baptiste", Decimal(-10)),
    ]


def test__operations__ChangeBalances__one_to_all(ledger_state):
    operation = ChangeBalances(amount=10, credit_to=None, debt_from=["baptiste"])
    assert operation.description == "transfering credit (10) from (baptiste) to (All)"
    assert operation.changes(ledger_state) == [
        BalanceChange("antoine", Decimal("3.34")),
        BalanceChange("baptiste", Decimal("3.33")),
        BalanceChange("renan", Decimal("3.33")),
        BalanceChange("baptiste", Decimal("-10.00")),
    ]


def test__operations__ChangeBalances__two_to_one(ledger_state):
    operation = ChangeBalances(
        amount=10, credit_to=["renan"], debt_from=["baptiste", "antoine"]
    )
    assert (
        operation.description
        == "transfering credit (10) from (baptiste, antoine) to (renan)"
    )
    assert operation.changes(ledger_state) == [
        BalanceChange("renan", Decimal("10")),
        BalanceChange("baptiste", Decimal("-5")),
        BalanceChange("antoine", Decimal("-5")),
    ]


def test__operations__ChangeBalances__two_to_two(ledger_state):
    operation = ChangeBalances(
        amount=10, credit_to=["renan", "baptiste"], debt_from=["baptiste", "antoine"]
    )
    assert (
        operation.description
        == "transfering credit (10) from (baptiste, antoine) to (renan, baptiste)"
    )
    assert operation.changes(ledger_state) == [
        BalanceChange("renan", Decimal("5")),
        BalanceChange("baptiste", Decimal("5")),
        BalanceChange("baptiste", Decimal("-5")),
        BalanceChange("antoine", Decimal("-5")),
    ]


def test__operations__ChangeBalances__two_to_all(ledger_state):
    operation = ChangeBalances(
        amount=10, credit_to=None, debt_from=["baptiste", "antoine"]
    )
    assert (
        operation.description
        == "transfering credit (10) from (baptiste, antoine) to (All)"
    )
    assert operation.changes(ledger_state) == [
        BalanceChange("antoine", Decimal("3.34")),
        BalanceChange("baptiste", Decimal("3.33")),
        BalanceChange("renan", Decimal("3.33")),
        BalanceChange("baptiste", Decimal("-5")),
        BalanceChange("antoine", Decimal("-5")),
    ]


def test__operations__ChangeBalances__all_to_one(ledger_state):
    operation = ChangeBalances(amount=10, credit_to=["antoine"], debt_from=None)
    assert operation.description == "transfering credit (10) from (All) to (antoine)"
    assert operation.changes(ledger_state) == [
        BalanceChange("antoine", Decimal("10")),
        BalanceChange("antoine", Decimal("-3.34")),
        BalanceChange("baptiste", Decimal("-3.33")),
        BalanceChange("renan", Decimal("-3.33")),
    ]


def test__operations__ChangeBalances__all_to_two(ledger_state):
    operation = ChangeBalances(
        amount=10, credit_to=["antoine", "baptiste"], debt_from=None
    )
    assert (
        operation.description
        == "transfering credit (10) from (All) to (antoine, baptiste)"
    )
    assert operation.changes(ledger_state) == [
        BalanceChange("antoine", Decimal("5")),
        BalanceChange("baptiste", Decimal("5")),
        BalanceChange("antoine", Decimal("-3.34")),
        BalanceChange("baptiste", Decimal("-3.33")),
        BalanceChange("renan", Decimal("-3.33")),
    ]


def test__operations__ChangeBalances__all_to_all(ledger_state):
    operation = ChangeBalances(amount=10, credit_to=None, debt_from=None)
    assert operation.description == "transfering credit (10) from (All) to (All)"
    assert operation.changes(ledger_state) == [
        BalanceChange("antoine", Decimal("3.34")),
        BalanceChange("baptiste", Decimal("3.33")),
        BalanceChange("renan", Decimal("3.33")),
        BalanceChange("antoine", Decimal("-3.34")),
        BalanceChange("baptiste", Decimal("-3.33")),
        BalanceChange("renan", Decimal("-3.33")),
    ]


def test__operations__SharedExpense(ledger_state):
    operation = SharedExpense(amount=100, by="antoine", subject="renting a van")
    assert operation.description == "antoine paid 100 for renting a van"
    assert operation.changes(ledger_state) == [
        BalanceChange("antoine", Decimal("100")),
        BalanceChange("antoine", Decimal("-33.34")),
        BalanceChange("baptiste", Decimal("-33.33")),
        BalanceChange("renan", Decimal("-33.33")),
    ]


def test__operations__Transfer(ledger_state):
    operation = Transfer(amount=100, by="baptiste", to="antoine")
    assert operation.description == "baptiste sends 100 to antoine"
    assert operation.changes(ledger_state) == [
        BalanceChange("baptiste", Decimal("100")),
        BalanceChange("antoine", Decimal("-100")),
    ]


# ------------------------ ledger ------------------------


@fixture
def ledger():
    ledger = Ledger()
    ledger.record_operation(AddAccount("antoine"))
    ledger.record_operation(AddAccount("baptiste"))
    ledger.record_operation(AddAccount("renan"))
    return ledger


def test__Ledger__create():
    ledger = Ledger()
    assert ledger.state == {}


def test__Ledger__add_account(ledger):
    ledger.record_operation(AddAccount("kriti"))
    assert list(ledger.state.keys()) == ["antoine", "baptiste", "renan", "kriti"]


def test__Ledger__add_account__error(ledger):
    with raises(RuntimeError):
        ledger.record_operation(AddAccount("antoine"))


def test__Ledger__remove_account(ledger):
    ledger.record_operation(RemoveAccount("antoine"))
    assert list(ledger.state.keys()) == ["baptiste", "renan"]


def test__Ledger__remove_account__error(ledger):
    with raises(RuntimeError):
        ledger.record_operation(RemoveAccount("kriti"))
    ledger.record_operation(Transfer(by="antoine", to="renan", amount=10))
    with raises(RuntimeError):
        ledger.record_operation(RemoveAccount("antoine"))


def test__Ledger__change_balance(ledger):
    ledger.record_operation(
        ChangeBalances(credit_to=None, debt_from=["antoine", "renan"], amount=100)
    )
    assert ledger.state == {
        "antoine": Decimal("-16.66"),
        "baptiste": Decimal("33.33"),
        "renan": Decimal("-16.67"),
    }


def test__Ledger__shared_expense(ledger):
    ledger.record_operation(SharedExpense(by="antoine", amount=100, subject="buy wood"))
    assert ledger.state == {
        "antoine": Decimal("66.66"),
        "baptiste": Decimal("-33.33"),
        "renan": Decimal("-33.33"),
    }


def test__Ledger__transfer(ledger):
    ledger.record_operation(Transfer(by="antoine", to="renan", amount=50))
    assert ledger.state == {
        "antoine": Decimal("50"),
        "baptiste": Decimal("0"),
        "renan": Decimal("-50"),
    }
