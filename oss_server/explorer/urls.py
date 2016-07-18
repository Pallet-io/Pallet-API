from django.conf.urls import url

from .v1.views import RetrieveBlockView

urlpatterns = [
    url('^v1/blocks$', RetrieveBlockView.as_view()),
]
