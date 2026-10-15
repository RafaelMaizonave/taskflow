from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class User:
    id: int
    email: str
    password_hash: str = field(repr=False)
    name: str = ""
    created_at: datetime | None = None
    token_version: int = 0
