import httplib

from django.conf import settings
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from gcoinrpc import connect_to_remote
from gcoinrpc.exceptions import InvalidAddressOrKey, InvalidParameter
from django.conf.urls import handler500


def get_rpc_connection():
    return connect_to_remote(settings.GCOIN_RPC['user'],
                             settings.GCOIN_RPC['password'],
                             settings.GCOIN_RPC['host'],
                             settings.GCOIN_RPC['port'])


def server_error(request):
    response = {"error": "internal server error"}
    return JsonResponse(response, status=httplib.INTERNAL_SERVER_ERROR)


class CsrfExemptMixin(object):
    """
    Exempts the view from CSRF requirements.

    This should be the left-most mixin of a view.
    """
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(CsrfExemptMixin, self).dispatch(*args, **kwargs)


class GetLicenseInfoView(CsrfExemptMixin, View):
    def get(self, request, color_id, *args, **kwargs):
        try:
            response = get_rpc_connection().getlicenseinfo(int(color_id))
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


class GetBalanceView(CsrfExemptMixin, View):
    def get(self, request, address, *args, **kwargs):
        utxos = get_rpc_connection().gettxoutaddress(address)
        balance_dict = self._count_balance_from_utxos(utxos)
        return JsonResponse(balance_dict)

    def _count_balance_from_utxos(self, utxos):
        balance_dict = {}
        if utxos:
            for txout in utxos:
                color = txout['color']
                value = txout['value']
                balance_dict[color] = (balance_dict.get(color) or 0) + value
        return balance_dict
