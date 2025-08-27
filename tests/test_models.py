import pathlib
from decimal import Decimal
from textwrap import dedent

from pytest import fixture, raises

from collective_accounting.models import (
    AccountCreation,
    AccountRemoval,
    AddAccount,
    BalanceChange,
    ChangeBalances,
    Ledger,
    LedgerState,
    Money,
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
        state._change_balance("baptiste", Money(10))


def test__LedgerState__check_balances(ledger_state):
    ledger_state._check_balances()
    ledger_state._change_balance("antoine", Money(10))
    with raises(RuntimeError):
        ledger_state._check_balances()
    ledger_state._change_balance("renan", Money(-5))
    ledger_state._change_balance("baptiste", Money(-5))
    ledger_state._check_balances()


def test__LedgerState__pot_creation(ledger_state):
    assert ledger_state.has_pot == False
    ledger_state._add_pot()
    assert ledger_state.has_pot == True


def test__LedgerState__pot_name_exclusive(ledger_state):
    with raises(RuntimeError):
        ledger_state._add_account("POT")


def test__LedgerState__pot_creation__two_times(ledger_state):
    ledger_state._add_pot()
    with raises(RuntimeError):
        ledger_state._add_pot()


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
    ledger_state._change_balance("baptiste", Money(12))
    with raises(RuntimeError):
        ledger_state.apply_change(AccountRemoval(name="baptiste"))


def test__LedgerState__apply_change__BalanceChange(ledger_state):
    ledger_state.apply_change(BalanceChange(name="antoine", amount=Money(12)))
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
            BalanceChange(name="antoine", amount=Money(10)),
            BalanceChange(name="renan", amount=Money(-5)),
            BalanceChange(name="baptiste", amount=Money(-5)),
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
                BalanceChange(name="antoine", amount=Money(10)),
                BalanceChange(name="renan", amount=Money(-5)),
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


def test__operations__AddPot(ledger_state):
    operation = AddPot()
    assert operation.TYPE == "Add Pot"
    assert operation.description == ""
    assert operation.changes(ledger_state) == [PotCreation()]


def test__operations__ChangeBalances__one_to_one(ledger_state):
    operation = ChangeBalances(
        amount=Money(10), credit_to=["antoine"], debt_from=["baptiste"]
    )
    assert operation.TYPE == "Change Balances"
    assert operation.description == "(10.00) owed by (baptiste), credited to (antoine)"
    assert operation.changes(ledger_state) == [
        BalanceChange("antoine", Money(10)),
        BalanceChange("baptiste", Money(-10)),
    ]


def test__operations__ChangeBalances__one_to_two(ledger_state):
    operation = ChangeBalances(
        amount=Money(10), credit_to=["antoine", "renan"], debt_from=["baptiste"]
    )
    assert (
        operation.description
        == "(10.00) owed by (baptiste), credited to (antoine, renan)"
    )
    assert operation.changes(ledger_state) == [
        BalanceChange("antoine", Money(5)),
        BalanceChange("renan", Money(5)),
        BalanceChange("baptiste", Money(-10)),
    ]


def test__operations__ChangeBalances__one_to_all(ledger_state):
    operation = ChangeBalances(amount=Money(10), credit_to=None, debt_from=["baptiste"])
    assert operation.description == "(10.00) owed by (baptiste), credited to (All)"
    assert operation.changes(ledger_state) == [
        BalanceChange("antoine", Money("3.34")),
        BalanceChange("baptiste", Money("3.33")),
        BalanceChange("renan", Money("3.33")),
        BalanceChange("baptiste", Money("-10.00")),
    ]


def test__operations__ChangeBalances__two_to_one(ledger_state):
    operation = ChangeBalances(
        amount=Money(10), credit_to=["renan"], debt_from=["baptiste", "antoine"]
    )
    assert (
        operation.description
        == "(10.00) owed by (baptiste, antoine), credited to (renan)"
    )
    assert operation.changes(ledger_state) == [
        BalanceChange("renan", Money("10")),
        BalanceChange("baptiste", Money("-5")),
        BalanceChange("antoine", Money("-5")),
    ]


def test__operations__ChangeBalances__two_to_two(ledger_state):
    operation = ChangeBalances(
        amount=Money(10),
        credit_to=["renan", "baptiste"],
        debt_from=["baptiste", "antoine"],
    )
    assert (
        operation.description
        == "(10.00) owed by (baptiste, antoine), credited to (renan, baptiste)"
    )
    assert operation.changes(ledger_state) == [
        BalanceChange("renan", Money("5")),
        BalanceChange("baptiste", Money("5")),
        BalanceChange("baptiste", Money("-5")),
        BalanceChange("antoine", Money("-5")),
    ]


def test__operations__ChangeBalances__two_to_all(ledger_state):
    operation = ChangeBalances(
        amount=Money(10), credit_to=None, debt_from=["baptiste", "antoine"]
    )
    assert (
        operation.description
        == "(10.00) owed by (baptiste, antoine), credited to (All)"
    )
    assert operation.changes(ledger_state) == [
        BalanceChange("antoine", Money("3.34")),
        BalanceChange("baptiste", Money("3.33")),
        BalanceChange("renan", Money("3.33")),
        BalanceChange("baptiste", Money("-5")),
        BalanceChange("antoine", Money("-5")),
    ]


def test__operations__ChangeBalances__all_to_one(ledger_state):
    operation = ChangeBalances(amount=Money(10), credit_to=["antoine"], debt_from=None)
    assert operation.description == "(10.00) owed by (All), credited to (antoine)"
    assert operation.changes(ledger_state) == [
        BalanceChange("antoine", Money("10")),
        BalanceChange("antoine", Money("-3.34")),
        BalanceChange("baptiste", Money("-3.33")),
        BalanceChange("renan", Money("-3.33")),
    ]


def test__operations__ChangeBalances__all_to_two(ledger_state):
    operation = ChangeBalances(
        amount=Money(10), credit_to=["antoine", "baptiste"], debt_from=None
    )
    assert (
        operation.description
        == "(10.00) owed by (All), credited to (antoine, baptiste)"
    )
    assert operation.changes(ledger_state) == [
        BalanceChange("antoine", Money("5")),
        BalanceChange("baptiste", Money("5")),
        BalanceChange("antoine", Money("-3.34")),
        BalanceChange("baptiste", Money("-3.33")),
        BalanceChange("renan", Money("-3.33")),
    ]


def test__operations__ChangeBalances__all_to_all(ledger_state):
    operation = ChangeBalances(amount=Money(10), credit_to=None, debt_from=None)
    assert operation.description == "(10.00) owed by (All), credited to (All)"
    assert operation.changes(ledger_state) == [
        BalanceChange("antoine", Money("3.34")),
        BalanceChange("baptiste", Money("3.33")),
        BalanceChange("renan", Money("3.33")),
        BalanceChange("antoine", Money("-3.34")),
        BalanceChange("baptiste", Money("-3.33")),
        BalanceChange("renan", Money("-3.33")),
    ]


def test__operations__SharedExpense(ledger_state):
    operation = SharedExpense(amount=Money(100), by="antoine", subject="renting a van")
    assert operation.description == "antoine has paid 100.00 for renting a van"
    assert operation.changes(ledger_state) == [
        BalanceChange("antoine", Money("100")),
        BalanceChange("antoine", Money("-33.34")),
        BalanceChange("baptiste", Money("-33.33")),
        BalanceChange("renan", Money("-33.33")),
    ]


def test__operations__Transfer(ledger_state):
    operation = Transfer(amount=Money(100), by="baptiste", to="antoine")
    assert operation.description == "baptiste has sent 100.00 to antoine"
    assert operation.changes(ledger_state) == [
        BalanceChange("baptiste", Money("100")),
        BalanceChange("antoine", Money("-100")),
    ]


# ------------------------ ledger ------------------------


@fixture
def ledger():
    ledger = Ledger()
    ledger.apply(AddAccount("antoine"))
    ledger.apply(AddAccount("baptiste"))
    ledger.apply(AddAccount("renan"))
    return ledger


def test__Ledger__create():
    ledger = Ledger()
    assert ledger.state == {}


def test__Ledger__add_account(ledger):
    ledger.apply(AddAccount("kriti"))
    assert list(ledger.state.keys()) == ["antoine", "baptiste", "renan", "kriti"]


def test__Ledger__add_account__error(ledger):
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


def test__Ledger__change_balance(ledger):
    ledger.apply(
        ChangeBalances(
            credit_to=None, debt_from=["antoine", "renan"], amount=Money(100)
        )
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


# ------------------------ IOs ------------------------


@fixture
def tmp_ledger_file(mocker, tmp_path):
    mocker.patch.object(Ledger, "LEDGER_FILE", tmp_path / Ledger.LEDGER_FILE)


@fixture
def ledger_with_operations(ledger):
    for operation in [
        AddAccount("kriti"),
        ChangeBalances(
            amount=Money(50), credit_to=["antoine"], debt_from=["renan", "baptiste"]
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
            credit_to:
            - antoine
            debt_from:
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
