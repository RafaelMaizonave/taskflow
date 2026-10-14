from dataclasses import dataclass, field


@dataclass(frozen=True)
class User:
    id: int
    email: str
    password_hash: str = field(repr=False)
