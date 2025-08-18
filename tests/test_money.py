from decimal import Decimal

from collective_accounting.money import divide, round_to_cent


def test__round_to_cent():
    assert round_to_cent(10) == Decimal("10")
    assert round_to_cent(10.123) == Decimal("10.12")


def test__divide():
    assert divide(Decimal(9), Decimal(3)) == (Decimal(3), Decimal(0))
    assert divide(Decimal(10), Decimal(3)) == (Decimal("3.33"), Decimal("0.01"))
    assert divide(Decimal(20), Decimal(3)) == (Decimal("6.67"), Decimal("-0.01"))
