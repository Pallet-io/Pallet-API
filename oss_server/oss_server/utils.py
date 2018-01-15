from __future__ import unicode_literals

import gcoin

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _


def address_validator(value):
    error = ValidationError(
        _('%(address)s is not a valid address'),
        code='invalid_address',
        params={'address': value}
    )
    if not gcoin.is_address(value):
        raise error
    try:
        gcoin.b58check_to_hex(value)
    except AssertionError:
        raise error

def amount_validator(value, min_value, max_value, decimal_places):
    if value < min_value:
        raise ValidationError(
            _('%(name)s `amount` should be greater than or equal to %(min_value)s'),
            code='invalid_amount',
            params={'min_value': min_value}
        )
    if value > max_value:
        raise ValidationError(
            _('%(name)s `amount` should be less than or equal to %(max_value)s'),
            code='invalid_amount',
            params={'max_value': max_value}
        )
    if abs(value.as_tuple().exponent) > decimal_places:
        raise ValidationError(
            _('%(name)s `amount` only allow up to %(decimal_places)s decimal digits'),
            code='invalid_amount',
            params={'decimal_places': decimal_places}
        )

def json_validator(value, required_keys):
    if not required_keys <= set(value.keys()):
        raise ValidationError(
            _('%(name)s objects should contain keys %(required_keys)s '),
            code='invalid_json',
            params={'required_keys': required_keys}
        )
