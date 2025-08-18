from decimal import Decimal


def round_to_cent(amount):
    return Decimal(amount).quantize(Decimal("0.01"))


def divide(amount: Decimal, denominator: Decimal) -> (Decimal, Decimal):
    quantized_result = round_to_cent(amount / denominator)
    remainder = amount - quantized_result * denominator
    return (quantized_result, remainder)
