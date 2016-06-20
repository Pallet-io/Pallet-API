from django.conf.urls import url

from .v1.views import (CreateRawTxView,
                       GetBalanceView,
                       GetLicenseInfoView,
                       GetRawTxView)

urlpatterns = [
    url('^v1/license/(?P<color_id>\d+)$', GetLicenseInfoView.as_view()),
    url('^v1/transaction/create$', CreateRawTxView.as_view()),
    url('^v1/transaction/(?P<tx_id>[a-z0-9]+)$', GetRawTxView.as_view()),
    url('^v1/balance/(?P<address>[a-zA-Z0-9]+)$', GetBalanceView.as_view()),
]
