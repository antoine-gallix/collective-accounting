import inspect
from operator import attrgetter

import funcy

from lausa import operations


def module_objects(module):
    return [getattr(operations, name) for name in dir(operations)]


def is_subclass_of(parent_class):
    return funcy.all_fn(
        inspect.isclass,
        funcy.rpartial(issubclass, parent_class),
        lambda x: x is not parent_class,
    )


operations_objects = module_objects(operations)
account_operation_classes = funcy.filter(
    is_subclass_of(operations.AccountOperation),
    operations_objects,
)
accounting_operation_classes = funcy.filter(
    is_subclass_of(operations.AccountingOperation),
    operations_objects,
)

print("--- Account Operations ---")
print("\n".join(list(funcy.map(attrgetter("__name__"), account_operation_classes))))
print("--- Accounting Operations ---")
print("\n".join(list(funcy.map(attrgetter("__name__"), accounting_operation_classes))))
