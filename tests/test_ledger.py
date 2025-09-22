import pathlib
from textwrap import dedent

from pytest import fixture

from collective_accounting.account import Account, PositiveAccount
from collective_accounting.ledger import Ledger
from collective_accounting.money import Money
from collective_accounting.operations import (
    AddAccount,
    AddPot,
    Debt,
    PaysContribution,
    Reimburse,
    RequestContribution,
    SharedExpense,
    Transfer,
    TransferDebt,
)


@fixture
def ledger():
    ledger = Ledger()
    ledger.add_account("antoine")
    ledger.add_account("baptiste")
    ledger.add_account("renan")
    return ledger


# -------- scenarios


def test__Ledger__create():
    ledger = Ledger()
    assert ledger.state == {}


def test__Ledger__scenario__populate_ledger():
    ledger = Ledger()
    ledger.add_account("antoine")
    ledger.add_account("baptiste")
    ledger.add_account("renan")
    assert ledger.operations == [
        AddAccount(name="antoine"),
        AddAccount(name="baptiste"),
        AddAccount(name="renan"),
    ]
    assert ledger.state == {
        "antoine": Account(balance=Money("0.00"), diff=Money("0.00")),
        "baptiste": Account(balance=Money("0.00"), diff=Money("0.00")),
        "renan": Account(balance=Money("0.00"), diff=Money("0.00")),
    }


def test__Ledger__scenario__shared_expense(ledger):
    ledger.record_shared_expense(amount=125, name="antoine", subject="potatoes")
    ledger.record_transfer(
        amount=30,
        sender="baptiste",
        receiver="antoine",
    )
    ledger.record_transfer_debt(40, "renan", "baptiste")
    ledger.record_debt(
        30, creditor="baptiste", debitor="renan", subject="lunch at baustelle"
    )
    assert ledger.operations == [
        AddAccount(name="antoine"),
        AddAccount(name="baptiste"),
        AddAccount(name="renan"),
        SharedExpense(
            amount=Money("125.00"),
            payer="antoine",
            subject="potatoes",
        ),
        Transfer(
            amount=Money("30.00"),
            sender="baptiste",
            receiver="antoine",
        ),
        TransferDebt(
            amount=Money("40.00"),
            old_debitor="renan",
            new_debitor="baptiste",
        ),
        Debt(
            amount=Money("30.00"),
            creditor="baptiste",
            debitor="renan",
            subject="lunch at baustelle",
        ),
    ]
    assert ledger.state == {
        "antoine": Account(balance=Money("-95.00"), diff=Money("53.34")),
        "baptiste": Account(balance=Money("-30.00"), diff=Money("-21.67")),
        "renan": Account(balance=Money("0.00"), diff=Money("-31.67")),
    }


def test__Ledger__scenario__pot(ledger):
    ledger.add_pot()
    ledger.request_contribution(50)
    ledger.pays_contribution(50, "antoine")
    ledger.pays_contribution(30, "baptiste")
    ledger.pays_contribution(50, "renan")
    ledger.record_shared_expense(amount=125, name="antoine", subject="potatoes")
    ledger.reimburse(100, "antoine")
    assert ledger.operations == [
        AddAccount(name="antoine"),
        AddAccount(name="baptiste"),
        AddAccount(name="renan"),
        AddPot(),
        RequestContribution(
            amount=Money("50.00"),
        ),
        PaysContribution(
            amount=Money("50.00"),
            sender="antoine",
        ),
        PaysContribution(
            amount=Money("30.00"),
            sender="baptiste",
        ),
        PaysContribution(
            amount=Money("50.00"),
            sender="renan",
        ),
        SharedExpense(
            amount=Money("125.00"),
            payer="antoine",
            subject="potatoes",
        ),
        Reimburse(
            amount=Money("100.00"),
            receiver="antoine",
        ),
    ]
    assert ledger.state == {
        "antoine": Account(balance=Money("-75.00"), diff=Money("25.00")),
        "baptiste": Account(balance=Money("-30.00"), diff=Money("-20.00")),
        "renan": Account(balance=Money("-50.00"), diff=Money("0.00")),
        "POT": PositiveAccount(balance=Money("30.00"), diff=Money("-5.00")),
    }


def test__Ledger__scenario__list_expenses(ledger):
    ledger.record_shared_expense(amount=125, name="antoine", subject="potatoes")
    ledger.record_shared_expense(amount=60, name="baptiste", subject="pumpkins")
    ledger.record_shared_expense(amount=30, name="renan", subject="endivias")
    ledger.record_shared_expense(amount=125, name="antoine", subject="onions")
    ledger.record_transfer(
        amount=30,
        sender="baptiste",
        receiver="antoine",
    )
    assert ledger.expenses == [
        SharedExpense(
            amount=Money("125.00"),
            payer="antoine",
            subject="potatoes",
            tags=(),
        ),
        SharedExpense(
            amount=Money("60.00"),
            payer="baptiste",
            subject="pumpkins",
            tags=(),
        ),
        SharedExpense(
            amount=Money("30.00"),
            payer="renan",
            subject="endivias",
            tags=(),
        ),
        SharedExpense(
            amount=Money("125.00"),
            payer="antoine",
            subject="onions",
            tags=(),
        ),
    ]


# -------- IO


@fixture
def tmp_ledger_file(mocker, tmp_path):
    mocker.patch.object(Ledger, "LEDGER_FILE", tmp_path / Ledger.LEDGER_FILE)


@fixture
def ledger_with_operations(ledger):
    ledger.add_pot()
    ledger.request_contribution(50)
    ledger.pays_contribution(50, "antoine")
    ledger.pays_contribution(30, "baptiste")
    ledger.pays_contribution(50, "renan")
    ledger.record_shared_expense(amount=125, name="antoine", subject="potatoes")
    ledger.reimburse(100, "antoine")
    return ledger


def test__Ledger__save_to_file(ledger_with_operations):
    ledger_with_operations.save_to_file()
    file_content = pathlib.Path(ledger_with_operations.LEDGER_FILE).read_text()
    assert file_content == dedent(
        """\
        operation: AddAccount
        name: antoine
        ---
        operation: AddAccount
        name: baptiste
        ---
        operation: AddAccount
        name: renan
        ---
        operation: AddPot
        ---
        operation: RequestContribution
        amount: 50.0
        ---
        operation: PaysContribution
        amount: 50.0
        sender: antoine
        ---
        operation: PaysContribution
        amount: 30.0
        sender: baptiste
        ---
        operation: PaysContribution
        amount: 50.0
        sender: renan
        ---
        operation: SharedExpense
        amount: 125.0
        payer: antoine
        subject: potatoes
        ---
        operation: Reimburse
        amount: 100.0
        receiver: antoine
        """
    )


def test__Ledger__load_from_file(ledger_with_operations, tmp_ledger_file):
    ledger_with_operations.save_to_file()
    ledger_loaded = Ledger.load_from_file()
    assert ledger_loaded.state == ledger_with_operations.state


def test__Ledger__edit(ledger, tmp_ledger_file):
    ledger.save_to_file()
    with Ledger.edit() as ledger_under_edit:
        ledger_under_edit.record_transfer(10, "antoine", "baptiste")
    ledger_loaded = Ledger.load_from_file()
    assert ledger_loaded.state == {
        "antoine": Account(
            balance=Money("-10.00"),
            diff=Money("10.00"),
        ),
        "baptiste": Account(
            balance=Money("10.00"),
            diff=Money("-10.00"),
        ),
        "renan": Account(
            balance=Money("0.00"),
            diff=Money("0.00"),
        ),
    }
    assert ledger_loaded.operations == [
        AddAccount(
            name="antoine",
        ),
        AddAccount(
            name="baptiste",
        ),
        AddAccount(
            name="renan",
        ),
        Transfer(
            amount=Money("10.00"),
            sender="antoine",
            receiver="baptiste",
        ),
    ]
    try:
        with Ledger.edit() as ledger_under_edit:
            ledger_under_edit.add_account("antoine")
    except RuntimeError:
        pass
    ledger_loaded_again = Ledger.load_from_file()
    assert ledger_loaded_again.state == ledger_loaded.state
    assert ledger_loaded_again.operations == ledger_loaded.operations
