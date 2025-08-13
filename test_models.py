from collective_accounting.models import Account, Group
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
    group = Group()
    group.add_account("antoine")
    group.add_account("baptiste")
    group.add_account("renan")
    return group


def test__group__from_file():
    raise NotImplementedError


def test__group__as_dict(group):
    assert group.as_dict() == {"antoine": 0, "baptiste": 0, "renan": 0}


def test__group__create():
    group = Group()
    assert group.as_dict() == {}


def test__group__add_account():
    g = Group()
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


def test__group__get(group):
    antoine = group.get("antoine")
    assert isinstance(antoine, Account)
    assert antoine.name == "antoine"
    assert antoine.credit == 0
    with pytest.raises(KeyError):
        group.get("finn")


def test__group__shared_credit(group):
    assert group.as_dict() == {"antoine": 0, "baptiste": 0, "renan": 0}
    group.add_shared_expense("antoine", 9)
    assert group.as_dict() == {"antoine": 6.0, "baptiste": -3.0, "renan": -3.0}
