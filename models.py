from dataclasses import dataclass, field


@dataclass
class Account:
    name: str
    credit: float = 0


@dataclass
class Group:
    accounts: list[Account] = field(default_factory=list)
