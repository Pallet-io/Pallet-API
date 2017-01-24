from __future__ import unicode_literals

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

import gcoin

from .utils import address_validator

__all__ = ('AddressField', 'ColorField', 'MintAmountField', 'PubkeyField', 'TxAmountField')


def pubkey_validator(value):
    error = ValidationError(
        _('%(pubkey)s is not a valid public key'),
        code='invalid',
        params={'pubkey': value}
    )
    if not gcoin.is_pubkey(value):
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


class PubkeyField(forms.CharField):
    def __init__(self, *args, **kwargs):
        super(PubkeyField, self).__init__(*args, **kwargs)
        self.validators.append(pubkey_validator)


class TxAmountField(forms.DecimalField):
    def __init__(self, *args, **kwargs):
        super(TxAmountField, self).__init__(decimal_places=8, max_value=10**10, min_value=0, *args, **kwargs)
