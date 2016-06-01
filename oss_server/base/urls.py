from django.conf.urls import url

from .v1.views import GetAssetInfoView

urlpatterns = [
    url('^v1/asset/(?P<color_id>\d+)$', GetAssetInfoView.as_view()),
]
