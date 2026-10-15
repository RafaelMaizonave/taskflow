from typing import Protocol

from app.domain.errors import AuthenticationError, PasswordMismatchError
from app.domain.user import User


class UserRepository(Protocol):
    def by_email(self, email: str) -> User | None: ...
    def by_id(self, user_id: int) -> User | None: ...
    def add(self, email: str, password_hash: str, name: str = "") -> User: ...
    def update(self, user_id: int, changes: dict) -> User: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...


class Passwords(Protocol):
    def hash(self, password: str) -> str: ...
    def verify(self, password_hash: str, password: str) -> bool: ...
    def dummy_verify(self, password: str) -> None: ...


class Tokens(Protocol):
    def issue(self, user_id: int, token_version: int = 0) -> str: ...
    def parse(self, token: str) -> tuple[int, int]: ...


class AuthService:
    def __init__(self, users: UserRepository, passwords: Passwords, tokens: Tokens):
        self.users = users
        self.passwords = passwords
        self.tokens = tokens

    def register(self, email: str, password: str, name: str = "") -> User:
        try:
            user = self.users.add(
                email.strip().casefold(), self.passwords.hash(password), name
            )
            self.users.commit()
            return user
        except Exception:
            self.users.rollback()
            raise

    def login(self, email: str, password: str) -> str:
        user = self.users.by_email(email.strip().casefold())
        if user is None:
            self.passwords.dummy_verify(password)
            raise AuthenticationError("Credenciais inválidas")
        if not self.passwords.verify(user.password_hash, password):
            raise AuthenticationError("Credenciais inválidas")
        return self.tokens.issue(user.id, user.token_version)

    def authenticate(self, token: str) -> User:
        user_id, token_version = self.tokens.parse(token)
        user = self.users.by_id(user_id)
        if user is None or user.token_version != token_version:
            raise AuthenticationError("Token inválido ou expirado")
        return user

    def update_profile(self, user_id: int, changes: dict) -> User:
        try:
            user = self.users.update(user_id, changes)
            self.users.commit()
            return user
        except Exception:
            self.users.rollback()
            raise

    def revoke_sessions(self, user_id: int) -> User:
        user = self.users.by_id(user_id)
        if user is None:
            raise AuthenticationError("Usuário não encontrado")
        return self.update_profile(user_id, {"token_version": user.token_version + 1})

    def change_password(self, user: User, current_password: str, password: str) -> str:
        if not self.passwords.verify(user.password_hash, current_password):
            raise PasswordMismatchError("Senha atual incorreta")
        updated = self.update_profile(
            user.id,
            {
                "password_hash": self.passwords.hash(password),
                "token_version": user.token_version + 1,
            },
        )
        return self.tokens.issue(updated.id, updated.token_version)
