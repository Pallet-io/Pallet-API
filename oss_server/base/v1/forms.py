from django import forms
from django.core.exceptions import ValidationError

from oss_server.fields import AddressField, PubkeyField, TxAmountField

class RawTxForm(forms.Form):
    from_address = AddressField(error_messages={
        'required': '`from_address` is required',
        'invalid': '`from_address` is not an address'
    })
    to_address = AddressField(error_messages={
        'required': '`to_address` is required',
        'invalid': '`to_address` is not an address'
    })
    amount = TxAmountField(error_messages={
        'required': '`amount` is required',
        'invalid': '`amount` is invalid',
        'min_value': '`amount` should be greater than or equal to %(limit_value)s',
        'max_value': '`amount` should be less than or equal to %(limit_value)s',
        'max_decimal_places': '`amount` only allow up to %(max)s decimal digits'
    })
    fee = TxAmountField(error_messages={
        'required': '`fee` is required',
        'invalid': '`fee` is invalid',
        'min_value': '`fee` should be greater than or equal to %(limit_value)s',
        'max_value': '`fee` should be less than or equal to %(limit_value)s',
        'max_decimal_places': '`fee` only allow up to %(max)s decimal digits'
    })
    op_return_data = forms.CharField(required=False)

    def clean_op_return_data(self):
        data = self.cleaned_data['op_return_data']
        if len(data.encode('utf8')) > 128000:
            raise forms.ValidationError('`op_return_data` exceed 128KB after encoded with utf-8', code='max_length')
        return data

