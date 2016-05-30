import httplib

from django.conf import settings
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from gcoinrpc import connect_to_remote
from gcoinrpc.exceptions import InvalidAddressOrKey, InvalidParameter


def get_rpc_connection():
    return connect_to_remote(settings.GCOIN_RPC['user'],
                             settings.GCOIN_RPC['password'],
                             settings.GCOIN_RPC['host'],
                             settings.GCOIN_RPC['port'])


class CsrfExemptMixin(object):
    """
    Exempts the view from CSRF requirements.

    This should be the left-most mixin of a view.
    """
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(CsrfExemptMixin, self).dispatch(*args, **kwargs)


class GetAssetInfoView(CsrfExemptMixin, View):
    def get(self, request, color_id, *args, **kwargs):
        try:
            response = get_rpc_connection().getassetinfo(int(color_id))
            return JsonResponse(response)
        except InvalidParameter:
            response = {'error': 'license color not exist'}
            return JsonResponse(response, status=httplib.NOT_FOUND)

class GetRawTransactionView(CsrfExemptMixin, View):
    def get(self, request, tx_id, *args, **kwargs):
        try:
            rpc = get_rpc_connection()
            response = rpc.getrawtransaction(tx_id)
            return JsonResponse(response.__dict__)
        except (InvalidParameter, InvalidAddressOrKey):
            response = {'error': 'transaction not found'}
            return JsonResponse(response, status=httplib.NOT_FOUND)

