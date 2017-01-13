from django.conf.urls import url

from .v1.views import *

urlpatterns = [
    url('^v1/addresses/(?P<address>[a-zA-Z0-9]+)/utxo$', UtxoView.as_view()),
    url('^v1/balance/(?P<address>[a-zA-Z0-9]+)$', GetBalanceView.as_view()),
    url('^v1/license/(?P<color_id>\d+)$', GetLicenseInfoView.as_view()),
    url('^v1/license/prepare', CreateLicenseRawTxView.as_view()),
    url('^v1/license/transfer/prepare$', CreateLicenseTransferRawTxView.as_view()),
    url('^v1/license/send$', SendRawTxView.as_view()),
    url('^v1/mint/prepare$', CreateMintRawTxView.as_view()),
    url('^v1/mint/send$', SendRawTxView.as_view()),
    url('^v1/smartcontract/prepare$', CreateSmartContractRawTxView.as_view()),
    url('^v1/smartcontract/send$', SendRawTxView.as_view()),
    url('^v1/transaction/prepare$', CreateRawTxView.as_view()),
    url('^v1/transaction/send$', SendRawTxView.as_view()),
    url('^v1/transaction/(?P<tx_id>[a-z0-9]+)$', GetRawTxView.as_view()),
]
