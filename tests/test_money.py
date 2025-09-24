from decimal import Decimal

from lausa.money import (
    Money,
)

# ------------------------ Money ------------------------


def test__Money__creation():
    assert Money(5) == 5 == Decimal("5")
    assert Money(-5) == -5 == Decimal("-5")
    assert Money(3.5) == Decimal("3.5")
    assert Money(12.345678) == Decimal("12.35")


def test__Money__str():
    assert str(Money(3.5)) == "3.50€"
    assert str(Money(-3.5)) == "-3.50€"


def test__Money__format():
    assert f"{Money(3.5)}" == "3.50€"
    assert f"{Money(3.5):+}" == "+3.50€"
    assert f"{Money(-3.5)}" == "-3.50€"
    assert f"{Money(-3.5):+}" == "-3.50€"


def test__Money__divide():
    assert Money(9).divide_with_no_rest(3) == [Money(3), Money(3), Money(3)]
    assert Money(10).divide_with_no_rest(3) == [
        Money("3.34"),
        Money("3.33"),
        Money("3.33"),
    ]
    assert Money(20).divide_with_no_rest(3) == [
        Money("6.66"),
        Money("6.67"),
        Money("6.67"),
    ]


def test__Money__add():
    assert Money(9) + Money(3) == Money(12)
    assert type(Money(9) + Money(3)) is Money


def test__Money__sub():
    assert Money(9) - Money(3) == Money(6)
    assert type(Money(9) - Money(3)) is Money


def test__Money__neg():
    assert -Money(3) == Money(-3)
    assert type(-Money(3)) is Money


def test__Money__div():
    assert Money(9) / Money(3) == Money(3)
    assert Money(10) / Money(3) == Money("3.33")
    assert type(Money(9) / Money(3)) is Money


def test__Money__mul():
    assert Money(9) * Money(3) == Money(27)
    assert type(Money(9) * Money(3)) is Money
