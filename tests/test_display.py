from collective_accounting.display import (
    describe_operation,
    file_creation_timestamp,
    file_modification_timestamp,
)
from collective_accounting.money import Money
from collective_accounting.operations import (
    AddAccount,
    AddPot,
    Debt,
    PaysContribution,
    Reimburse,
    RemoveAccount,
    RequestContribution,
    SharedExpense,
    Transfer,
    TransferDebt,
)

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


# ------------------------ operation description ------------------------


def test__describe__AddAccount():
    assert describe_operation(AddAccount("antoine")).markup == "[blue]antoine[/blue]"


def test__describe__RemoveAccount():
    assert describe_operation(RemoveAccount("antoine")).markup == "[blue]antoine[/blue]"


def test__describe__AddPot():
    assert describe_operation(AddPot()).markup == "Add a common pot to the group"


# --- money movement
def test__describe__SharedExpense():
    assert (
        describe_operation(
            SharedExpense(amount=Money(100), payer="antoine", subject="renting a van")
        ).markup
        == "[blue]antoine[/blue] pays [green]100.00€[/green] for [yellow]renting a van[/yellow]"
    )


def test__describe__SharedExpense__tags():
    # one tag
    assert (
        describe_operation(
            SharedExpense(
                amount=Money(100),
                payer="antoine",
                subject="kitchen tent",
                tags=("asset",),
            )
        ).markup
        == "[blue]antoine[/blue] pays [green]100.00€[/green] for [yellow]kitchen tent[/yellow] \[asset]"
    )
    # two tags
    assert (
        describe_operation(
            SharedExpense(
                amount=Money(100),
                payer="antoine",
                subject="kitchen tent",
                tags=("asset", "kitchen"),
            )
        ).markup
        == "[blue]antoine[/blue] pays [green]100.00€[/green] for [yellow]kitchen tent[/yellow] \[asset, kitchen]"
    )


def test__describe__Transfer():
    assert (
        describe_operation(
            Transfer(amount=Money(100), sender="baptiste", receiver="antoine")
        ).markup
        == "[blue]baptiste[/blue] sends [green]100.00€[/green] to [blue]antoine[/blue]"
    )


def test__describe__Reimburse():
    assert (
        describe_operation(Reimburse(Money(50), "antoine")).markup
        == "Reimburse [green]50.00€[/green] to [blue]antoine[/blue] from the pot"
    )


def test__describe__PaysContribution():
    assert (
        describe_operation(PaysContribution(amount=Money(100), sender="antoine")).markup
        == "[blue]antoine[/blue] contributes [green]100.00€[/green] to the pot"
    )


# --- debt movement
def test__describe__Debt():
    assert (
        describe_operation(
            Debt(amount=Money(10), debitor="renan", creditor="antoine", subject="lunch")
        ).markup
        == "[blue]renan[/blue] owes [green]10.00€[/green] to [blue]antoine[/blue] for [yellow]lunch[/yellow]"
    )


def test__describe__RequestContribution():
    assert (
        describe_operation(RequestContribution(Money(100))).markup
        == "Request contribution of [green]100.00€[/green] from everyone"
    )


def test__describe__TransferDebt():
    assert (
        describe_operation(
            TransferDebt(amount=Money(100), old_debitor="baptiste", new_debitor="renan")
        ).markup
        == "[blue]renan[/blue] covers [green]100.00€[/green] of debt from [blue]baptiste[/blue]"
    )
