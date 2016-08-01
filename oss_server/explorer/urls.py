from django.conf.urls import url

from .v1.views import (GetAddressBalanceView,
                       GetAddressTxsView,
                       GetAddressUtxoView,
                       GetBlockByHashView,
                       GetBlockByHeightView,
                       GetColorTxsView,
                       GetLatestBlocksView,
                       GetTxByHashView)

urlpatterns = [
    url('^v1/blocks$', GetLatestBlocksView.as_view()),
    url('^v1/blocks/(?P<block_hash>[A-Za-z0-9]{64})', GetBlockByHashView.as_view()),
    url('^v1/blocks/(?P<block_height>\d{1,10})', GetBlockByHeightView.as_view()),
    url('^v1/transactions/(?P<tx_hash>[A-Za-z0-9]{64})', GetTxByHashView.as_view()),
    url('^v1/transactions/color/(?P<color_id>\d{1,10})', GetColorTxsView.as_view()),
    url('^v1/transactions/address/(?P<address>[13][a-km-zA-HJ-NP-Z1-9]{26,33})', GetAddressTxsView.as_view()),
    url('^v1/addresses/(?P<address>[13][a-km-zA-HJ-NP-Z1-9]{26,33})/balance', GetAddressBalanceView.as_view()),
    url('^v1/addresses/(?P<address>[13][a-km-zA-HJ-NP-Z1-9]{26,33})/utxos', GetAddressUtxoView.as_view()),
]
