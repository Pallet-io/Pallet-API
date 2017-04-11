import httplib

from django.http import JsonResponse, Http404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import CreateView, DeleteView, DetailView

from .forms import AddressSubscriptionModelForm, TxSubscriptionModelForm
from ..models import AddressSubscription, TxSubscription


def invalid_params_response(errors):
    params = []
    for field, error_list in errors.items():
        params.append({
            "name": field,
            "message": ",".join(error_list)
        })

    response = {
        "error": {
            "type": "invalid_request_error",
            "params": params
        }
    }
    return JsonResponse(response, status=httplib.BAD_REQUEST)


class CsrfExemptMixin(object):
    """
    Exempts the view from CSRF requirements.

    This should be the left-most mixin of a view.
    """
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(CsrfExemptMixin, self).dispatch(*args, **kwargs)


class BaseSubscriptionCreateView(CsrfExemptMixin, CreateView):
    http_method_names = [u'post']

    def form_invalid(self, form):
        return invalid_params_response(form.errors)

    def form_valid(self, form):
        self.object = form.save()
        response = self.object.as_dict()
        return JsonResponse(response, status=httplib.OK)


class BaseSubscriptionDetailView(DetailView):
    http_method_names = [u'get']

    def get(self, request, *args, **kwargs):
        try:
            return super(BaseSubscriptionDetailView, self).get(request, *args, **kwargs)
        except Http404:
            response = {
                "error": {
                    "type": "invalid_request_error",
                    "params": [
                        {
                            "name": "id",
                            "message": "not found"
                        }
                    ]
                }
            }
            return JsonResponse(response, status=httplib.NOT_FOUND)

    def render_to_response(self, context, **response_kwargs):
        obj = context['object']
        response = obj.as_dict()
        return JsonResponse(response, status=httplib.OK)


class BaseSubscriptionDeleteView(CsrfExemptMixin, DeleteView):
    success_url = "dummy/url"
    http_method_names = [u'post']

    def delete(self, request, *args, **kwargs):
        try:
            object_id = self.get_object().pk
        except Http404:
            response = {
                "error": {
                    "type": "invalid_request_error",
                    "params": [
                        {
                            "name": "id",
                            "message": "not found"
                        }
                    ]
                }
            }
            return JsonResponse(response, status=httplib.NOT_FOUND)

        super(DeleteView, self).delete(request, *args, **kwargs)
        response = {
            "id": str(object_id),
            "deleted": True
        }
        return JsonResponse(response, status=httplib.OK)


class AddressSubscriptionCreateView(BaseSubscriptionCreateView):
    model = AddressSubscription
    form_class = AddressSubscriptionModelForm


class TxSubscriptionCreateView(BaseSubscriptionCreateView):
    model = TxSubscription
    form_class = TxSubscriptionModelForm

class AddressSubscriptionDetailView(BaseSubscriptionDetailView):
    model = AddressSubscription


class TxSubscriptionDetailView(BaseSubscriptionDetailView):
    model = TxSubscription


class AddressSubscriptionDeleteView(BaseSubscriptionDeleteView):
    model = AddressSubscription

class TxSubscriptionDeleteView(BaseSubscriptionDeleteView):
    model = TxSubscription

