"""Password-hashing regression coverage for the retained bcrypt contract."""

import bcrypt
import pytest

from backend.core.security import get_password_hash, verify_password


def test_password_hash_verifies_only_the_correct_password():
    hashed = get_password_hash("correct horse battery staple")
    assert hashed.startswith("$2b$")
    assert verify_password("correct horse battery staple", hashed)
    assert not verify_password("wrong password", hashed)


def test_existing_bcrypt_hash_remains_compatible():
    # Existing Passlib bcrypt hashes use the standard bcrypt encoding.
    hashed = bcrypt.hashpw(b"existing-password", bcrypt.gensalt(prefix=b"2a")).decode()
    assert verify_password("existing-password", hashed)
    assert not verify_password("incorrect", hashed)


def test_overlong_password_is_rejected_without_truncation():
    password = "a" * 72
    hashed = get_password_hash(password)
    assert verify_password(password, hashed)
    with pytest.raises(ValueError, match="72 UTF-8 bytes"):
        get_password_hash(password + "a")
    assert not verify_password(password + "a", hashed)
    with pytest.raises(ValueError, match="72 UTF-8 bytes"):
        get_password_hash("é" * 37)


def test_invalid_hash_returns_false():
    assert not verify_password("password", "not a bcrypt hash")
