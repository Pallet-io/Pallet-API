from __future__ import unicode_literals

import gcoin

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _


def address_validator(value):
    error = ValidationError(
        _('%(address)s is not a valid address'),
        code='invalid',
        params={'address': value}
    )
    if not gcoin.is_address(value):
        raise error
    try:
        gcoin.b58check_to_hex(value)
    except AssertionError:
        raise error
