from django.conf.urls import url

from .v1.views import (GetAddressBalanceView,
                       GetAddressOpReturnView,
                       GetAddressTxsView,
                       GetAddressUtxoView,
                       GetBlockByHashView,
                       GetBlockByHeightView,
                       GetBlocksView,
                       GetTxByIDView,
                       GeneralTxExplorerView,
                       CreateRawTxExplorerView)

urlpatterns = [
    url('^v1/blocks$', GetBlocksView.as_view()),
    url('^v1/blocks/(?P<block_hash>[A-Za-z0-9]{64})', GetBlockByHashView.as_view()),
    url('^v1/blocks/(?P<block_height>\d{1,10})', GetBlockByHeightView.as_view()),
    url('^v1/transactions/(?P<txid>[A-Za-z0-9]{64})', GetTxByIDView.as_view()),
    url('^v1/transactions/address/(?P<address>[123mn][a-km-zA-HJ-NP-Z1-9]{26,33})', GetAddressTxsView.as_view()),
    url('^v1/general-transaction/prepare$', GeneralTxExplorerView.as_view()),
    url('^v1/transaction/prepare$', CreateRawTxExplorerView.as_view()),
    url('^v1/addresses/(?P<address>[123mn][a-km-zA-HJ-NP-Z1-9]{26,33})/balance', GetAddressBalanceView.as_view()),
    url('^v1/addresses/(?P<address>[123mn][a-km-zA-HJ-NP-Z1-9]{26,33})/op_return', GetAddressOpReturnView.as_view()),
    url('^v1/addresses/(?P<address>[123mn][a-km-zA-HJ-NP-Z1-9]{26,33})/utxos', GetAddressUtxoView.as_view()),
]
