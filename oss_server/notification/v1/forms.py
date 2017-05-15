from django import forms

from ..models import AddressSubscription, TxSubscription

class AddressSubscriptionModelForm(forms.ModelForm):
    class Meta:
        model = AddressSubscription
        fields = ['address', 'callback_url', 'confirmation']
        error_messages = {
            'address': {
                'required': 'address is required',
                'invalid': 'address is invalid',
            },
            'callback_url': {
                'required': 'callback_url is required',
                'invalid': 'callback_url is invalid',
            },
            'confirmation': {
                'required': 'confirmation is required',
            }
        }

class TxSubscriptionModelForm(forms.ModelForm):
    class Meta:
        model = TxSubscription
        fields = ['tx_hash', 'confirmation_count', 'callback_url']
        error_messages = {
            'tx_hash': {
                'required': 'tx_hash is required',
                'invalid': 'tx_hash is invalid',
                'max_length': 'tx_hash is at most %(limit_value)s characters'
            },
            'confirmation_count': {
                'required': 'confirmation_count is required',
                'invalid': 'confirmation_count is invalid',
                'min_value': 'confirmation_count needs to be greater than or equal to 1'
            },
            'callback_url': {
                'required': 'callback_url is required',
                'invalid': 'callback_url is invalid',
            }
        }
