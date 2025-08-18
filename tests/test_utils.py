from decimal import Decimal

from collective_accounting.utils import divide, round_to_cent, timestamp

# ------------------------ decimal ------------------------


def test__round_to_cent():
    assert round_to_cent(10) == Decimal("10")
    assert round_to_cent(10.123) == Decimal("10.12")


def test__divide():
    assert divide(Decimal(9), Decimal(3)) == (Decimal(3), Decimal(0))
    assert divide(Decimal(10), Decimal(3)) == (Decimal("3.33"), Decimal("0.01"))
    assert divide(Decimal(20), Decimal(3)) == (Decimal("6.67"), Decimal("-0.01"))


# ------------------------ file ------------------------


def test__timestamp(tmp_path):
    file = tmp_path / "file"
    # no file
    assert timestamp(file) is None
    # timestamp is a stable number
    file.write_text("something")
    first_timestamp = timestamp(file)
    assert first_timestamp is not None
    assert isinstance(first_timestamp, float)
    assert timestamp(file) == first_timestamp
    # timestamp changes after a write
    file.write_text("something more")
    second_timestamp = timestamp(file)
    assert second_timestamp > first_timestamp
