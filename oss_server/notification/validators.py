from django.core.exceptions import ValidationError

from gcoin import is_address, b58check_to_hex


def validate_address(value):
    if not is_address(value):
        raise ValidationError(
            "%(value)s is not a valid address",
            params={'value': value},
        )

    try:
        b58check_to_hex(value)
    except AssertionError:
        raise ValidationError(
            "%(value)s is not a valid address",
            params={'value': value},
        )

