from unittest.mock import Mock

import pytest

from app.application.auth import AuthService
from app.domain.errors import AuthenticationError, ConflictError
from app.domain.user import User
from app.infrastructure.auth import ArgonPasswords, JwtTokens


def test_register_normalizes_email_and_commits():
    users, passwords, tokens = Mock(), Mock(), Mock()
    service = AuthService(users, passwords, tokens)
    service.register(" Rafael@Example.com ", "password")
    users.add.assert_called_once_with(
        "rafael@example.com", passwords.hash.return_value, ""
    )
    users.commit.assert_called_once()


def test_register_rolls_back_conflict():
    users = Mock()
    users.add.side_effect = ConflictError("Duplicado")
    service = AuthService(users, Mock(), Mock())
    with pytest.raises(ConflictError):
        service.register("rafael@example.com", "password")
    users.rollback.assert_called_once()
    users.commit.assert_not_called()


def test_unknown_user_performs_dummy_verification():
    users, passwords = Mock(), Mock()
    users.by_email.return_value = None
    with pytest.raises(AuthenticationError):
        AuthService(users, passwords, Mock()).login("missing@example.com", "password")
    passwords.dummy_verify.assert_called_once_with("password")


def test_wrong_password_never_issues_token():
    users, passwords, tokens = Mock(), Mock(), Mock()
    users.by_email.return_value = User(1, "rafael@example.com", "hash")
    passwords.verify.return_value = False
    with pytest.raises(AuthenticationError):
        AuthService(users, passwords, tokens).login("rafael@example.com", "password")
    tokens.issue.assert_not_called()


def test_hashes_are_salted_and_verified():
    passwords = ArgonPasswords()
    first, second = passwords.hash("password"), passwords.hash("password")
    assert first != second
    assert passwords.verify(first, "password")
    assert not passwords.verify(first, "incorrect")
    assert not passwords.verify("invalid-hash", "password")


def test_tokens_round_trip(settings):
    tokens = JwtTokens(settings)
    assert tokens.parse(tokens.issue(42, 3)) == (42, 3)


def test_authenticate_rejects_revoked_token_version():
    users, passwords, tokens = Mock(), Mock(), Mock()
    tokens.parse.return_value = (1, 0)
    users.by_id.return_value = User(1, "rafael@example.com", "hash", token_version=1)
    with pytest.raises(AuthenticationError):
        AuthService(users, passwords, tokens).authenticate("token")


def test_change_password_issues_token_with_new_version():
    users, passwords, tokens = Mock(), Mock(), Mock()
    user = User(1, "rafael@example.com", "hash", token_version=2)
    passwords.verify.return_value = True
    passwords.hash.return_value = "new-hash"
    users.update.return_value = User(
        1, "rafael@example.com", "new-hash", token_version=3
    )
    tokens.issue.return_value = "new-token"
    service = AuthService(users, passwords, tokens)
    assert service.change_password(user, "atual", "Nova-senha-123") == "new-token"
    users.update.assert_called_once_with(
        1, {"password_hash": "new-hash", "token_version": 3}
    )
    tokens.issue.assert_called_once_with(1, 3)


def test_password_hash_is_absent_from_user_repr():
    assert "secret-hash" not in repr(User(1, "rafael@example.com", "secret-hash"))
