import pytest

from felix.validators import validate_email


@pytest.mark.parametrize("email", [
    "users@gmail.com",
    "foo@bar.com",
    "AbCDeFG@123.com",
])
def test_validate_email_valid(email):
    validate_email(email)

@pytest.mark.parametrize("invalid_email", [
    "missingatsignatcommonmail.com",
    "missingdotcom",
])
def test_validate_email_invalid(invalid_email):
    with pytest.raises(ValueError):
        validate_email(invalid_email)
