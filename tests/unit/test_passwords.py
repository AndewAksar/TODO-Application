import pytest
from services.api_gateway.app.security.passwords import hash_password, verify_password


def test_hash_password_returns_string_and_not_plain() -> None:
    plain_password = "password0123456789"
    hashed_password = hash_password(plain_password)

    # Check if the hashed password is a string
    assert isinstance(hashed_password, str)

    # Check if the hashed password is different from the plain password
    assert hashed_password != plain_password

    # Check if the hashed password starts with the expected prefix
    assert hashed_password.startswith("$2")


def test_hash_password_is_salted_and_changes_each_time() -> None:
    plain_password = "password0123456789"
    hashed_password_1 = hash_password(plain_password)
    hashed_password_2 = hash_password(plain_password)

    # Check if the hashed passwords are different
    assert hashed_password_1 != hashed_password_2

    # Check if the hashed passwords are correct
    assert verify_password(plain_password, hashed_password_1) is True
    assert verify_password(plain_password, hashed_password_2) is True


def test_verify_password_true_for_correct_password() -> None:
    plain_password = "correct_password0123456789"
    hashed_password = hash_password(plain_password)

    # Check if the password is verified correctly
    assert verify_password(plain_password, hashed_password) is True


def test_verify_password_false_for_incorrect_password() -> None:
    hashed_password = hash_password("correct_password0123456789")

    # Check if the password is verified correctly
    assert verify_password("incorrect_password0123456789", hashed_password) is False


def test_verify_password_false_for_broken_hash_string() -> None:
    broken_hash = "this-is-not-a-valid-hash"

    # Check if the password is verified correctly
    assert verify_password("any_password", broken_hash) is False


@pytest.mark.parametrize(
    "plain, hashed",
    [
        (None, "x"),
        ("x", None),
        (123, "x"),
        ("x", 123),
    ],
)
def test_verify_password_type_validation(plain, hashed) -> None:
    with pytest.raises(TypeError):
        verify_password(plain, hashed)


@pytest.mark.parametrize("bad_password", ["", None, 123, 0.5, [], {}])
def test_hash_password_rejects_invalid_input(bad_password) -> None:
    if bad_password == "":
        with pytest.raises(ValueError):
            hash_password(bad_password)
    else:
        with pytest.raises(TypeError):
            hash_password(bad_password)
