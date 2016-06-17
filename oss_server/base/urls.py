from django.conf.urls import url

from .v1.views import GetLicenseInfoView, GetRawTransactionView

urlpatterns = [
    url('^v1/license/(?P<color_id>\d+)$', GetLicenseInfoView.as_view()),
    url('^v1/transaction/(?P<tx_id>[a-z0-9]+)$', GetRawTransactionView.as_view()),
]
