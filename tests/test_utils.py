from decimal import Decimal

from collective_accounting.utils import (
    Money,
    divide,
    file_creation_timestamp,
    file_modification_timestamp,
    round_to_cent,
)

# ------------------------ Money ------------------------


def test__Money__creation():
    assert Money(5) == 5 == Decimal("5")
    assert Money(-5) == -5 == Decimal("-5")
    assert Money(3.5) == Decimal("3.5")
    assert Money(12.345678) == Decimal("12.35")


def test__Money__str():
    assert str(Money(3.5)) == "3.50€"


def test__Money__divide():
    assert Money(9).divide(3) == [Money(3), Money(3), Money(3)]
    assert Money(10).divide(3) == [Money("3.34"), Money("3.33"), Money("3.33")]
    assert Money(20).divide(3) == [Money("6.66"), Money("6.67"), Money("6.67")]


def test__Money__add_type():
    assert type(Money(9) + Money(3)) == Money


# ------------------------ decimal ------------------------


def test__round_to_cent():
    assert round_to_cent(10) == Decimal("10")
    assert round_to_cent(10.123) == Decimal("10.12")


def test__divide():
    assert divide(Decimal(9), 3) == [Decimal(3), Decimal(3), Decimal(3)]
    assert divide(Decimal(10), 3) == [Decimal("3.34"), Decimal("3.33"), Decimal("3.33")]
    assert divide(Decimal(20), 3) == [Decimal("6.66"), Decimal("6.67"), Decimal("6.67")]


# ------------------------ file ------------------------


def test__modification_timestamp(tmp_path):
    file = tmp_path / "file"
    # no file
    assert file_modification_timestamp(file) is None
    # timestamp is a stable number
    file.write_text("something")
    first_timestamp = file_modification_timestamp(file)
    assert first_timestamp is not None
    assert isinstance(first_timestamp, float)
    assert file_modification_timestamp(file) == first_timestamp
    # timestamp changes after a write
    file.write_text("something more")
    second_timestamp = file_modification_timestamp(file)
    assert second_timestamp > first_timestamp


def test__creation_timestamp(tmp_path):
    file = tmp_path / "file"
    # no file: None
    assert file_creation_timestamp(file) is None
    # indicates creation time
    file.write_text("something")
    first_timestamp = file_creation_timestamp(file)
    assert isinstance(first_timestamp, float)
    # do not change over time
    assert file_creation_timestamp(file) == first_timestamp
    # ... even after a update
    file.write_text("something more")
    assert file_creation_timestamp(file) == first_timestamp
