import inspect
from operator import attrgetter

import funcy

from collective_accounting import operations

operations_objects = (getattr(operations, name) for name in dir(operations))
operations_classes = funcy.filter(
    funcy.all_fn(inspect.isclass, funcy.rpartial(issubclass, operations.Operation)),
    operations_objects,
)
operations_names = funcy.map(attrgetter("__name__"), operations_classes)

print("\n".join(list(operations_names)))
