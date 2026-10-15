from datetime import UTC, datetime, timedelta
from functools import lru_cache

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.errors import AuthenticationError, ConflictError
from app.domain.user import User
from app.infrastructure.config import Settings
from app.infrastructure.database.models import UserModel


class SqlUserRepository:
    def __init__(self, session: Session):
        self.session = session

    @staticmethod
    def _user(model: UserModel | None) -> User | None:
        return (
            User(
                model.id,
                model.email,
                model.password_hash,
                model.name,
                model.created_at.replace(tzinfo=UTC) if model.created_at else None,
            )
            if model
            else None
        )

    def by_email(self, email: str) -> User | None:
        return self._user(
            self.session.scalar(select(UserModel).where(UserModel.email == email))
        )

    def by_id(self, user_id: int) -> User | None:
        return self._user(self.session.get(UserModel, user_id))

    def add(self, email: str, password_hash: str, name: str = "") -> User:
        model = UserModel(email=email, password_hash=password_hash, name=name)
        self.session.add(model)
        try:
            self.session.flush()
        except IntegrityError as error:
            raise ConflictError("E-mail já cadastrado") from error
        return self._user(model)

    def update(self, user_id: int, changes: dict) -> User:
        model = self.session.get(UserModel, user_id)
        if model is None:
            raise AuthenticationError("Usuário não encontrado")
        for key, value in changes.items():
            setattr(model, key, value)
        try:
            self.session.flush()
        except IntegrityError as error:
            raise ConflictError("E-mail já cadastrado") from error
        return self._user(model)

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()


class ArgonPasswords:
    def __init__(self):
        self.hasher = PasswordHasher()
        self.dummy = self.hash("dummy-password-for-timing-only")

    def hash(self, password: str) -> str:
        return self.hasher.hash(password)

    def verify(self, password_hash: str, password: str) -> bool:
        try:
            return self.hasher.verify(password_hash, password)
        except (VerificationError, InvalidHashError):
            return False

    def dummy_verify(self, password: str) -> None:
        self.verify(self.dummy, password)


@lru_cache(maxsize=1)
def get_passwords() -> ArgonPasswords:
    return ArgonPasswords()


class JwtTokens:
    def __init__(self, settings: Settings):
        self.secret = settings.jwt_secret.get_secret_value()
        self.minutes = settings.access_token_expire_minutes

    def issue(self, user_id: int) -> str:
        now = datetime.now(UTC)
        return jwt.encode(
            {
                "sub": str(user_id),
                "iat": now,
                "exp": now + timedelta(minutes=self.minutes),
            },
            self.secret,
            algorithm="HS256",
        )

    def subject(self, token: str) -> int:
        try:
            claims = jwt.decode(
                token,
                self.secret,
                algorithms=["HS256"],
                options={"require": ["sub", "exp", "iat"]},
            )
            subject = claims["sub"]
            if (
                not isinstance(subject, str)
                or not subject.isascii()
                or not subject.isdecimal()
                or not 1 <= int(subject) <= 2**63 - 1
            ):
                raise ValueError("invalid subject")
            if type(claims["exp"]) not in (int, float) or type(claims["iat"]) not in (
                int,
                float,
            ):
                raise ValueError("invalid timestamp")
            return int(subject)
        except (jwt.InvalidTokenError, ValueError, TypeError, OverflowError) as error:
            raise AuthenticationError("Token inválido ou expirado") from error
