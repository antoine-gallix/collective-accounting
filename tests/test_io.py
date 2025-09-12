from collective_accounting.io import load_operation_from_dict, operation_as_dict
from collective_accounting.money import Money
from collective_accounting.operations import (
    AddAccount,
    AddPot,
    PaysContribution,
    Reimburse,
    RemoveAccount,
    RequestContribution,
    SharedExpense,
    Transfer,
    TransferDebt,
)


def test__AddAccount():
    operation = AddAccount("antoine")
    operation_dict = operation_as_dict(operation)
    assert operation_dict == {"name": "antoine", "operation": "AddAccount"}
    assert load_operation_from_dict(operation_dict) == operation


def test__RemoveAccount():
    operation = RemoveAccount("antoine")
    operation_dict = operation_as_dict(operation)
    assert operation_dict == {"name": "antoine", "operation": "RemoveAccount"}
    assert load_operation_from_dict(operation_dict) == operation


def test__AddPot():
    operation = AddPot()
    operation_dict = operation_as_dict(operation)
    assert operation_dict == {"operation": "AddPot"}
    assert load_operation_from_dict(operation_dict) == operation


def test__SharedExpense():
    operation = SharedExpense(amount=Money(10), payer="antoine", subject="potatoes")
    operation_dict = operation_as_dict(operation)
    assert operation_dict == {
        "operation": "SharedExpense",
        "amount": 10.0,
        "payer": "antoine",
        "subject": "potatoes",
    }
    assert load_operation_from_dict(operation_dict) == operation


def test__TransferDebt():
    operation = TransferDebt(
        amount=Money(10), old_debitor="antoine", new_debitor="antoine"
    )
    operation_dict = operation_as_dict(operation)
    assert operation_dict == {
        "operation": "TransferDebt",
        "amount": 10.0,
        "old_debitor": "antoine",
        "new_debitor": "antoine",
    }
    assert load_operation_from_dict(operation_dict) == operation


def test__RequestContribution():
    operation = RequestContribution(amount=Money(100))
    operation_dict = operation_as_dict(operation)
    assert operation_dict == {
        "operation": "RequestContribution",
        "amount": 100.0,
    }
    assert load_operation_from_dict(operation_dict) == operation


def test__Transfer():
    operation = Transfer(amount=Money(100), sender="antoine", receiver="baptiste")
    operation_dict = operation_as_dict(operation)
    assert operation_dict == {
        "operation": "Transfer",
        "amount": 100.0,
        "sender": "antoine",
        "receiver": "baptiste",
    }
    assert load_operation_from_dict(operation_dict) == operation


def test__Reimburse():
    operation = Reimburse(amount=Money(100), receiver="baptiste")
    operation_dict = operation_as_dict(operation)
    assert operation_dict == {
        "operation": "Reimburse",
        "amount": 100.0,
        "receiver": "baptiste",
    }
    assert load_operation_from_dict(operation_dict) == operation


def test__PaysContribution():
    operation = PaysContribution(amount=Money(100), sender="baptiste")
    operation_dict = operation_as_dict(operation)
    assert operation_dict == {
        "operation": "PaysContribution",
        "amount": 100.0,
        "sender": "baptiste",
    }
    assert load_operation_from_dict(operation_dict) == operation
