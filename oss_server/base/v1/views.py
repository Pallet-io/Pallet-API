import httplib
import logging

from django.conf import settings
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from gcoin import make_raw_tx
from gcoinrpc import connect_to_remote
from gcoinrpc.exceptions import InvalidAddressOrKey, InvalidParameter

from .forms import RawTxForm
from ..utils import balance_from_utxos, select_utxo

logger = logging.getLogger(__name__)


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


class GetLicenseInfoView(View):
    def get(self, request, color_id, *args, **kwargs):
        try:
            response = get_rpc_connection().getlicenseinfo(int(color_id))
            return JsonResponse(response)
        except InvalidParameter:
            response = {'error': 'license color not exist'}
            return JsonResponse(response, status=httplib.NOT_FOUND)


class GetRawTxView(View):
    def get(self, request, tx_id, *args, **kwargs):
        try:
            rpc = get_rpc_connection()
            response = rpc.getrawtransaction(tx_id)
            return JsonResponse(response.__dict__)
        except (InvalidParameter, InvalidAddressOrKey):
            response = {'error': 'transaction not found'}
            return JsonResponse(response, status=httplib.NOT_FOUND)


class CreateRawTxView(View):
    def get(self, request, *args, **kwargs):
        form = RawTxForm(request.GET)
        if form.is_valid():
            from_address = form.cleaned_data['from_address']
            to_address = form.cleaned_data['to_address']
            color_id = form.cleaned_data['color_id']
            amount = form.cleaned_data['amount']

            utxos = get_rpc_connection().gettxoutaddress(from_address)
            # Color 1 is used as fee, so here's special case for it.
            if color_id == 1:
                if not select_utxo(utxos, color_id, amount):
                    return JsonResponse({'error': 'insufficient funds'}, status=httplib.BAD_REQUEST)
                inputs = select_utxo(utxos, color_id, amount + 1)
                if not inputs:
                    return JsonResponse({'error': 'insufficient fee'}, status=httplib.BAD_REQUEST)
            else:
                inputs = select_utxo(utxos, color_id, amount)
                if not inputs:
                    return JsonResponse({'error': 'insufficient funds'}, status=httplib.BAD_REQUEST)
                fee = select_utxo(utxos, 1, 1)
                if not fee:
                    return JsonResponse({'error': 'insufficient fee'}, status=httplib.BAD_REQUEST)
                inputs += fee

            ins = [{'tx_id': utxo['txid'], 'index': utxo['vout']} for utxo in inputs]
            outs = [{'address': to_address, 'value': int(amount * 1e8), 'color': color_id}]
            # Now for the `change` part.
            if color_id == 1:
                inputs_value = balance_from_utxos(inputs)[color_id]
                change = inputs_value - amount - 1
                if change:
                    outs.append({'address': from_address, 'value': int(change * 10**8), 'color': color_id})
            else:
                inputs_value = balance_from_utxos(inputs)[color_id]
                change = inputs_value - amount
                if change:
                    outs.append({'address': from_address, 'value': int(change * 10**8), 'color': color_id})
                # Fee `change`.
                fee_value = balance_from_utxos(inputs)[1]
                fee_change = fee_value - 1
                if fee_change:
                    outs.append({'address': from_address, 'value': int(fee_change * 10**8), 'color': 1})

            raw_tx = make_raw_tx(ins, outs)
            return JsonResponse({'raw_tx': raw_tx})
        else:
            errors = ', '.join(reduce(lambda x, y: x + y, form.errors.values()))
            response = {'error': errors}
            return JsonResponse(response, status=httplib.BAD_REQUEST)


class SendRawTxView(CsrfExemptMixin, View):
    def post(self, request, *args, **kwargs):
        raw_tx = request.POST.get('raw_tx', '')
        try:
            tx_id = get_rpc_connection().sendrawtransaction(raw_tx)
            response = {'tx_id': tx_id}
            return JsonResponse(response)
        except:
            logger.error('Invalid transaction: %s', raw_tx, extra={'endpoint': request.path})
            response = {'error': 'invalid raw transaction'}
            return JsonResponse(response, status=httplib.BAD_REQUEST)


class GetBalanceView(View):
    def get(self, request, address, *args, **kwargs):
        utxos = get_rpc_connection().gettxoutaddress(address)
        balance_dict = balance_from_utxos(utxos)
        return JsonResponse(balance_dict)
