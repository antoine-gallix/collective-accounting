from dataclasses import asdict

import funcy

from . import operations
from .money import Money
from .operations import Operation


def money_to_float(obj):
    if isinstance(obj, Money):
        return float(obj)
    else:
        return obj


def number_to_money(obj):
    if isinstance(obj, (float, int)):
        return Money(obj)
    else:
        return obj


def operation_as_dict(operation: Operation) -> dict:
    op_as_dict = {"operation": operation.__class__.__name__} | asdict(operation)
    return funcy.walk_values(money_to_float, op_as_dict)  # type:ignore


def load_operation_from_dict(op_as_dict) -> Operation:
    classname = op_as_dict.pop("operation")
    operation_class = getattr(operations, classname)
    dict_transformed = funcy.walk_values(number_to_money, op_as_dict)
    return operation_class(**dict_transformed)  # type:ignore
