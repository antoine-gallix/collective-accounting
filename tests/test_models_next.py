from decimal import Decimal

from pytest import fixture, raises

from collective_accounting.models_next import Accounts, Ledger, Operation

# ------------------------ fixtures ------------------------


@fixture
def accounts_3():
    accounts = Accounts()
    accounts.add_account("antoine")
    accounts.add_account("baptiste")
    accounts.add_account("renan")
    return accounts


# ------------------------ accounts ------------------------


def test__Accounts__creation():
    accounts = Accounts()
    assert accounts == {}


def test__Accounts__add_account():
    accounts = Accounts()
    accounts.add_account("antoine")
    assert accounts == {"antoine": 0}


def test__Accounts__add_account__constraints():
    accounts = Accounts()
    # empty string
    with raises(ValueError):
        accounts.add_account("")
    # not a string
    with raises(TypeError):
        accounts.add_account(12)


def test__Accounts__add_account__existing_name():
    accounts = Accounts()
    accounts.add_account("antoine")
    with raises(ValueError):
        accounts.add_account("antoine")


def test__Accounts__change_balance():
    accounts = Accounts()
    accounts.add_account("antoine")
    accounts.change_balance("antoine", 10)
    assert accounts == {"antoine": 10}


def test__Accounts__name_do_not_exist():
    accounts = Accounts()
    accounts.add_account("antoine")
    with raises(ValueError):
        accounts.change_balance("baptiste", 10)


def test__Accounts__balanced():
    accounts = Accounts()
    accounts.add_account("antoine")
    accounts.add_account("baptiste")
    accounts.add_account("renan")
    accounts.change_balance("antoine", 10)
    assert accounts == {
        "antoine": 10,
        "baptiste": 0,
        "renan": 0,
    }
    with raises(RuntimeError):
        accounts.check_balances()


# ------------------------ operations ------------------------


def test_Operation(accounts_3):
    operation = Operation()
    assert operation.TYPE == "Base Operation"
    assert operation.description == "nothing happens"
    assert accounts_3 == {
        "antoine": 0,
        "baptiste": 0,
        "renan": 0,
    }
    operation.apply(accounts_3)
    assert accounts_3 == {
        "antoine": 0,
        "baptiste": 0,
        "renan": 0,
    }
    operation.apply(accounts_3)
    assert accounts_3 == {
        "antoine": 0,
        "baptiste": 0,
        "renan": 0,
    }


# ------------------------ ledger ------------------------


def test__Ledger__create():
    ledger = Ledger()
    assert ledger.accounts == {}
    assert ledger.operations == []
