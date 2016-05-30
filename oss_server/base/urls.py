from django.conf.urls import url

from .v1.views import GetAssetInfoView, GetRawTransactionView

urlpatterns = [
    url('^v1/asset/(?P<color_id>\d+)$', GetAssetInfoView.as_view()),
    url('^v1/transaction/(?P<tx_id>[a-z0-9]+)$', GetRawTransactionView.as_view()),
]
