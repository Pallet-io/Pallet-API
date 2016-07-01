from django import forms
from django.core.exceptions import ValidationError


class CreateLicenseInfoForm(forms.Form):
    address = forms.RegexField(r'^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$',
                               error_messages={
                                   'required': '`address` is required',
                                   'invalid': '`address` is not an address'
                               })
    color_id = forms.IntegerField(error_messages={'required': '`color_id` is required'})
    name = forms.CharField(max_length=32,
                           error_messages={
                               'required': '`name` is required',
                               'max_length': 'length of `name` should not exceed 32'
                           })
    description = forms.CharField(max_length=40,
                                  error_messages={
                                      'required': '`description` is required',
                                      'max_length': 'length of `description` should not exceed 40'
                                  })
    metadata_link = forms.CharField(max_length=255, required=False,
                                    error_messages={
                                        'max_length': 'length of `metadata_link` should not exceed 255'
                                    })
    member_control = forms.BooleanField(required=False,
                                        error_messages={'required': '`member_control` is required'})


class RawTxForm(forms.Form):
    from_address = forms.RegexField(r'^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$',
                                    error_messages={
                                        'required': '`from_address` is required',
                                        'invalid': '`from_address` is not an address'
                                    })
    to_address = forms.RegexField(r'^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$',
                                  error_messages={
                                      'required': '`to_address` is required',
                                      'invalid': '`to_address` is not an address'
                                  })
    color_id = forms.IntegerField(min_value=0,
                                  error_messages={
                                      'required': '`color_id` is required',
                                      'invalid': '`color_id` is invalid',
                                      'min_value': '`color_id` should be greater than 0'
                                  })
    amount = forms.DecimalField(min_value=0,
                                decimal_places=8,
                                error_messages={
                                    'required': '`amount` is required',
                                    'invalid': '`amount` is invalid',
                                    'min_value': '`amount` should be greater than 0',
                                    'max_decimal_places': '`amount` only allow up to 8 decimal digits'
                                })


class MintRawTxForm(forms.Form):
    mint_address = forms.RegexField(r'^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$',
                                    error_messages={
                                        'required': '`mint_address` is required',
                                        'invalid': '`mint_address` is not an address'
                                    })
    color_id = forms.IntegerField(min_value=0,
                                  error_messages={
                                      'required': '`color_id` is required',
                                      'invalid': '`color_id` is invalid',
                                      'min_value': '`color_id` should be greater than 0'
                                  })
    amount = forms.DecimalField(min_value=0,
                                decimal_places=8,
                                error_messages={
                                    'required': '`amount` is required',
                                    'invalid': '`amount` is invalid',
                                    'min_value': '`amount` should be greater than 0',
                                    'max_decimal_places': '`amount` only allow up to 8 decimal digits'
                                })

    def clean(self):
        cleaned_data = super(MintRawTxForm, self).clean()
        color_id = cleaned_data.get('color_id')
        amount = cleaned_data.get('amount')

        if color_id == 0 and amount and amount != 1:
            raise ValidationError('can only mint 1 `color 0` at one time', code='invalid')
