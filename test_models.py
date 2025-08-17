from collective_accounting.models import Account, Ledger
import pytest

# Account


def test__account__create():
    a = Account("antoine")
    assert a.credit == 0


def test__account__change_credit():
    a = Account("antoine")
    assert a.credit == 0
    a.change_credit(5)
    assert a.credit == 5
    a.change_credit(-8)
    assert a.credit == -3


# apply change to credit

# Group


@pytest.fixture
def group():
    group = Ledger()
    group.add_account("antoine")
    group.add_account("baptiste")
    group.add_account("renan")
    return group


# IOs


def test__file_IO(group, mocker, tmp_path):
    group._get_one("antoine").change_credit(10)
    group.get_one("renan").change_credit(-10)
    assert group.as_dict() == {"antoine": 10, "baptiste": 0, "renan": -10}
    mocker.patch.object(Ledger, "LEDGER_FILE", tmp_path / Ledger.LEDGER_FILE)
    group.save_to_file()
    imported_group = Ledger.load_from_file()
    assert imported_group.as_dict() == group.as_dict()


def test__group__as_dict(group):
    assert group.as_dict() == {"antoine": 0, "baptiste": 0, "renan": 0}


def test__group__create():
    group = Ledger()
    assert group.as_dict() == {}


def test__group__add_account():
    g = Ledger()
    antoine = g.add_account("antoine")
    assert g.as_dict() == {"antoine": 0}
    assert len(g.accounts) == 1
    assert isinstance(antoine, Account)
    assert antoine.name == "antoine"
    assert antoine.credit == 0
    nilou = g.add_account("nilou")
    assert len(g.accounts) == 2
    assert nilou.name == "nilou"
    assert nilou.credit == 0

    assert g.as_dict() == {"antoine": 0, "nilou": 0}


def test__group__get_one(group):
    antoine = group.get_one("antoine")
    assert isinstance(antoine, Account)
    assert antoine.name == "antoine"
    assert antoine.credit == 0
    with pytest.raises(KeyError):
        group.get_one("finn")


def test__group__get(group):
    # one
    group.get("antoine") == group.get_one("antoine")
    # one that does not exist
    with pytest.raises(KeyError):
        group.get("god")
    # list
    assert group.get(["antoine", "renan"]) == [Account("antoine"), Account("renan")]
    # list with one that does not exist
    with pytest.raises(KeyError):
        group.get(["jesus", "renan"])
    # all
    assert group.get("ALL") == [
        Account("antoine"),
        Account("baptiste"),
        Account("renan"),
    ]


# balance operation


def test__change_balances__to_one_from_one(group):
    group.credit(10, credit_to="antoine", debt_from="baptiste")
    assert group.as_dict() == {"antoine": 10.0, "baptiste": -10.0, "renan": 0}


def test__change_balances__to_one_from_list(group):
    group.credit(10, credit_to="antoine", debt_from=["baptiste", "renan"])
    assert group.as_dict() == {"antoine": 10.0, "baptiste": -5, "renan": -5}


def test__change_balances__to_one_from_all(group):
    group.credit(12, credit_to="antoine", debt_from="ALL")
    assert group.as_dict() == {"antoine": 8, "baptiste": -4, "renan": -4}


def test__change_balances__to_two_from_one(group):
    group.credit(12, credit_to=["antoine", "renan"], debt_from="baptiste")
    assert group.as_dict() == {"antoine": 6, "baptiste": -12, "renan": 6}


def test__change_balances__to_all_from_one(group):
    group.credit(12, credit_to="ALL", debt_from="antoine")
    assert group.as_dict() == {"antoine": -8, "baptiste": 4, "renan": 4}


def test__group__shared_credit(group):
    assert group.as_dict() == {"antoine": 0, "baptiste": 0, "renan": 0}
    group.add_shared_expense("antoine", 9)
    assert group.as_dict() == {"antoine": 6.0, "baptiste": -3.0, "renan": -3.0}
