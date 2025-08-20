from decimal import Decimal

from collective_accounting.utils import (
    divide,
    file_creation_timestamp,
    file_modification_timestamp,
    round_to_cent,
)

# ------------------------ decimal ------------------------


def test__round_to_cent():
    assert round_to_cent(10) == Decimal("10")
    assert round_to_cent(10.123) == Decimal("10.12")


def test__divide():
    assert divide(Decimal(9), Decimal(3)) == (Decimal(3), Decimal(0))
    assert divide(Decimal(10), Decimal(3)) == (Decimal("3.33"), Decimal("0.01"))
    assert divide(Decimal(20), Decimal(3)) == (Decimal("6.67"), Decimal("-0.01"))


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
