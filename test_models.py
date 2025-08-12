from models import Account, Group

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


def test__group__create():
    g = Group()
    assert len(g.accounts) == 0


def test__group__add_account():
    g = Group()
    antoine = g.add_account("antoine")
    assert len(g.accounts) == 1
    assert isinstance(antoine, Account)
    assert antoine.name == "antoine"
    assert antoine.credit == 0
    nilou = g.add_account("nilou")
    assert len(g.accounts) == 2
    assert nilou.name == "nilou"
    assert nilou.credit == 0


def test__group__shared_credit():
    g = Group()
    antoine = g.add_account("antoine")
    baptiste = g.add_account("baptiste")
    renan = g.add_account("renan")
    assert antoine.credit == 0
    assert baptiste.credit == 0
    assert renan.credit == 0
