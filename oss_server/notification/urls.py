from django.conf.urls import url

from .v1.views import AddressSubscriptionCreateView, TxSubscriptionCreateView
from .v1.views import AddressSubscriptionDetailView, TxSubscriptionDetailView
from .v1.views import AddressSubscriptionDeleteView, TxSubscriptionDeleteView

urlpatterns = [
    url(r'^v1/address/subscription$', AddressSubscriptionCreateView.as_view()),
    url(r'^v1/address/subscription/(?P<pk>[0-9a-z-]{36})$', AddressSubscriptionDetailView.as_view()),
    url(r'^v1/address/subscription/(?P<pk>[0-9a-z-]{36})/delete$', AddressSubscriptionDeleteView.as_view()),
    url(r'^v1/tx/subscription$', TxSubscriptionCreateView.as_view()),
    url(r'^v1/tx/subscription/(?P<pk>[0-9a-z-]{36})$', TxSubscriptionDetailView.as_view()),
    url(r'^v1/tx/subscription/(?P<pk>[0-9a-z-]{36})/delete$', TxSubscriptionDeleteView.as_view()),
]
