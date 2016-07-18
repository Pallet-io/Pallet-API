from django.conf.urls import url

from .v1.views import GetLatestBlocksView, GetBlockByHash, GetBlockByHeight

urlpatterns = [
    url('^v1/blocks$', GetLatestBlocksView.as_view()),
    url('^v1/blocks/(?P<block_hash>[A-Za-z0-9]{64})', GetBlockByHash.as_view()),
    url('^v1/blocks/(?P<block_height>\d{1,10})', GetBlockByHeight.as_view()),
]
