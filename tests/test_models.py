import pytest

from collective_accounting.models import Account, Ledger

# ------------------------ Account ------------------------


def test__account__create():
    a = Account("antoine")
    assert a.balance == 0


def test__account__change_credit():
    a = Account("antoine")
    assert a.balance == 0
    a.change_credit(5)
    assert a.balance == 5
    a.change_credit(-8)
    assert a.balance == -3


# ------------------------ Ledger ------------------------


@pytest.fixture
def tmp_ledger_file(mocker, tmp_path):
    mocker.patch.object(Ledger, "LEDGER_FILE", tmp_path / Ledger.LEDGER_FILE)


@pytest.fixture
def new_ledger():
    ledger = Ledger()
    ledger.add_account("antoine")
    ledger.add_account("baptiste")
    ledger.add_account("renan")
    return ledger


@pytest.fixture
def ledger(new_ledger):
    new_ledger.add_shared_expense(amount=12, by="antoine")
    return new_ledger


@pytest.fixture
def saved_ledger(ledger, tmp_ledger_file):
    ledger.save_to_file()
    return ledger


# --------


def test__Ledger__create():
    ledger = Ledger()
    assert ledger.as_dict() == {}


def test__Ledger__as_dict(ledger):
    assert ledger.as_dict() == {"antoine": 8, "baptiste": -4, "renan": -4}


# -------- IOs


def test__Ledger__file_IO(ledger, mocker, tmp_path):
    assert ledger.as_dict() == {"antoine": 8, "baptiste": -4, "renan": -4}
    ledger.save_to_file()
    loaded_ledger = Ledger.load_from_file()
    assert loaded_ledger.as_dict() == ledger.as_dict()


def test__Ledger__context_manager(saved_ledger):
    assert saved_ledger.as_dict() == {"antoine": 8.0, "baptiste": -4.0, "renan": -4.0}
    with Ledger.edit() as managed_ledger:
        managed_ledger.add_shared_expense(amount=21, by="antoine")
    loaded_ledger = Ledger.load_from_file()
    assert loaded_ledger.as_dict() == {
        "antoine": 22.0,
        "baptiste": -11.0,
        "renan": -11.0,
    }


# -------- Accounts management


def test__Ledger__add_account():
    ledger = Ledger()
    antoine = ledger.add_account("antoine")
    assert ledger.as_dict() == {"antoine": 0}
    assert len(ledger.accounts) == 1
    assert isinstance(antoine, Account)
    assert antoine.name == "antoine"
    assert antoine.balance == 0
    nilou = ledger.add_account("nilou")
    assert len(ledger.accounts) == 2
    assert nilou.name == "nilou"
    assert nilou.balance == 0

    assert ledger.as_dict() == {"antoine": 0, "nilou": 0}


def test__Ledger__add_account__unique_name():
    ledger = Ledger()
    ledger.add_account("antoine")
    with pytest.raises(ValueError):
        ledger.add_account("antoine")


def test__Ledger__get_one(ledger):
    antoine = ledger._get_one("antoine")
    assert isinstance(antoine, Account)
    assert antoine.name == "antoine"
    assert antoine.balance == 8
    with pytest.raises(KeyError):
        ledger._get_one("finn")


def test__Ledger__get(ledger):
    # one
    ledger.get("antoine") == ledger.get("antoine")

    # one that does not exist
    with pytest.raises(KeyError):
        ledger.get("god")

    # list
    assert ledger.get(["antoine", "renan"]) == [
        Account("antoine", balance=8),
        Account("renan", balance=-4),
    ]
    # list with one that does not exist
    with pytest.raises(KeyError):
        ledger.get(["jesus", "renan"])

    # all
    assert ledger.get("ALL") == [
        Account("antoine", balance=8),
        Account("baptiste", balance=-4),
        Account("renan", balance=-4),
    ]


# balance operation


def test__Ledger__change_balances__to_one_from_one(ledger):
    assert ledger.as_dict() == {"antoine": 8, "baptiste": -4, "renan": -4}
    ledger._credit(10, credit_to="antoine", debt_from="baptiste")
    assert ledger.as_dict() == {"antoine": 18, "baptiste": -14, "renan": -4}


def test__Ledger__change_balances__to_one_from_list(ledger):
    assert ledger.as_dict() == {"antoine": 8, "baptiste": -4, "renan": -4}
    ledger._credit(10, credit_to="antoine", debt_from=["baptiste", "renan"])
    assert ledger.as_dict() == {"antoine": 18, "baptiste": -9, "renan": -9}


def test__Ledger__change_balances__to_one_from_all(ledger):
    assert ledger.as_dict() == {"antoine": 8, "baptiste": -4, "renan": -4}
    ledger._credit(12, credit_to="antoine", debt_from="ALL")
    assert ledger.as_dict() == {"antoine": 16, "baptiste": -8, "renan": -8}


def test__Ledger__change_balances__to_two_from_one(ledger):
    assert ledger.as_dict() == {"antoine": 8, "baptiste": -4, "renan": -4}
    ledger._credit(12, credit_to=["antoine", "renan"], debt_from="baptiste")
    assert ledger.as_dict() == {"antoine": 14, "baptiste": -16, "renan": 2}


def test__Ledger__change_balances__to_all_from_one(ledger):
    assert ledger.as_dict() == {"antoine": 8, "baptiste": -4, "renan": -4}
    ledger._credit(12, credit_to="ALL", debt_from="antoine")
    assert ledger.as_dict() == {"antoine": 0, "baptiste": 0, "renan": 0}


def test__Ledger__add_shared_expense(ledger):
    assert ledger.as_dict() == {"antoine": 8, "baptiste": -4, "renan": -4}
    ledger.add_shared_expense("antoine", 9)
    assert ledger.as_dict() == {"antoine": 14, "baptiste": -7, "renan": -7}
