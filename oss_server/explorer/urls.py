from django.conf.urls import url

from .v1.views import GetLatestBlocksView, GetBlockByHashView, GetBlockByHeightView, GetTxByHashView

urlpatterns = [
    url('^v1/blocks$', GetLatestBlocksView.as_view()),
    url('^v1/blocks/(?P<block_hash>[A-Za-z0-9]{64})', GetBlockByHashView.as_view()),
    url('^v1/blocks/(?P<block_height>\d{1,10})', GetBlockByHeightView.as_view()),
    url('^v1/transactions/(?P<tx_hash>[A-Za-z0-9]{64})', GetTxByHashView.as_view()),
]
