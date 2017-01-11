from django import forms


class GetAddressTxsForm(forms.Form):
    starting_after = forms.CharField(required=False, min_length=64, max_length=64,
                                     error_messages={
                                         'invalid': '`starting_after` is invalid',
                                         'min_length': 'length of `starting_after` should be exactly 64',
                                         'max_length': 'length of `starting_after` should be exactly 64'
                                     })
    tx_type = forms.IntegerField(required=False, min_value=0, max_value=5,
                                 error_messages={
                                     'invalid': '`tx_type` is invalid',
                                     'min_value': '`tx_type` should be greater than or equal to %(limit_value)s',
                                     'max_value': '`tx_type` should be less than or equal to %(limit_value)s'
                                 })
    since = forms.IntegerField(required=False, min_value=0,
                               error_messages={
                                   'invalid': '`since` is invalid',
                                   'min_value': '`since` should be greater than or equal to %(limit_value)s'
                               })
    until = forms.IntegerField(required=False, min_value=0,
                               error_messages={
                                   'invalid': '`until` is invalid',
                                   'min_value': '`until` should be greater than or equal to %(limit_value)s'
                               })
    page_size = forms.IntegerField(required=False, min_value=0,
                                   error_messages={
                                       'invalid': '`page_size` is invalid',
                                       'min_value': '`page_size` should be greater than or equal to %(limit_value)s'
                                   })


class GetColorTxsForm(forms.Form):
    starting_after = forms.CharField(required=False, min_length=64, max_length=64,
                                     error_messages={
                                         'invalid': '`starting_after` is invalid',
                                         'min_length': 'length of `starting_after` should be exactly 64',
                                         'max_length': 'length of `starting_after` should be exactly 64'
                                     })
    since = forms.IntegerField(required=False, min_value=0,
                               error_messages={
                                   'invalid': '`since` is invalid',
                                   'min_value': '`since` should be greater than or equal to %(limit_value)s'
                               })
    until = forms.IntegerField(required=False, min_value=0,
                               error_messages={
                                   'invalid': '`until` is invalid',
                                   'min_value': '`until` should be greater than or equal to %(limit_value)s'
                               })
    page_size = forms.IntegerField(required=False, min_value=0,
                                   error_messages={
                                       'invalid': '`page_size` is invalid',
                                       'min_value': '`page_size` should be greater than or equal to %(limit_value)s'
                                   })
