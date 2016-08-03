from __future__ import unicode_literals

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

import gcoin

__all__ = ('AddressField', 'ColorField', 'MintAmountField', 'TxAmountField')


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


class AddressField(forms.CharField):
    def __init__(self, *args, **kwargs):
        super(AddressField, self).__init__(*args, **kwargs)
        self.validators.append(address_validator)


class ColorField(forms.IntegerField):
    def __init__(self, *args, **kwargs):
        super(ColorField, self).__init__(max_value=2**32-1, min_value=0, *args, **kwargs)


class MintAmountField(forms.IntegerField):
    def __init__(self, *args, **kwargs):
        super(MintAmountField, self).__init__(max_value=10**10, min_value=1, *args, **kwargs)


class TxAmountField(forms.DecimalField):
    def __init__(self, *args, **kwargs):
        super(TxAmountField, self).__init__(decimal_places=8, max_value=10**10, min_value=0, *args, **kwargs)
