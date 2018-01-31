from decimal import Decimal
import httplib
import json
import logging

from django.conf import settings
from django.core.validators import DecimalValidator
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from gcoin import (make_raw_tx, mk_op_return_script)
from gcoinrpc import connect_to_remote
from gcoinrpc.exceptions import InvalidAddressOrKey, InvalidParameter

from oss_server.utils import address_validator, amount_validator, json_validator
from oss_server.exceptions import TransactionError

from ..utils import balance_from_utxos, select_utxo, utxo_to_txin
from .forms import RawTxForm

logger = logging.getLogger(__name__)


def get_rpc_connection():
    return connect_to_remote(settings.BITCOIN_RPC['user'],
                             settings.BITCOIN_RPC['password'],
                             settings.BITCOIN_RPC['host'],
                             settings.BITCOIN_RPC['port'])


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


class GetRawTxView(View):

    def get(self, request, tx_id, *args, **kwargs):
        try:
            response = get_rpc_connection().getrawtransaction(tx_id)
            tx = self._to_explorer_style(response.__dict__)
            return JsonResponse(tx)
        except (InvalidParameter, InvalidAddressOrKey):
            response = {'error': 'transaction not found'}
            return JsonResponse(response, status=httplib.NOT_FOUND)

    def _to_explorer_style(self, base_tx):
        base_tx['hash'] = base_tx['txid']
        del base_tx['txid']

        base_tx['vins'] = base_tx['vin']
        del base_tx['vin']

        base_tx['vouts'] = base_tx['vout']
        del base_tx['vout']

        for index, vin in enumerate(base_tx['vins']):
            if hasattr(base_tx['vins'][index], 'txid'):
                base_tx['vins'][index]['tx_hash'] = base_tx['vins'][index]['txid']
                del base_tx['vins'][index]['txid']

        for index, vout in enumerate(base_tx['vouts']):
            if hasattr(base_tx['vouts'][index], 'value'):
                base_tx['vouts'][index]['amount'] = base_tx['vouts'][index]['value']
                del base_tx['vouts'][index]['value']

        return base_tx


class CreateTx(object):

    @staticmethod
    def _fetch_utxo(address):
        raise NotImplementedError

    @staticmethod
    def _aggregate_inputs(tx_in_list):
        tx_ins = {}

        for tx_in in tx_in_list:
            from_address = tx_in['from_address']
            tx_ins.setdefault(from_address, {'amount': 0, 'fee': 0})
            tx_ins[from_address]['amount'] += tx_in['amount']
            tx_ins[from_address]['fee'] += tx_in['fee']

        return tx_ins

    @staticmethod
    def _aggregate_outputs(tx_out_list):
        tx_outs = {}

        for tx_out in tx_out_list:
            to_address = tx_out['to_address']
            tx_outs.setdefault(to_address, 0)
            tx_outs[to_address] += tx_out['amount']

        return tx_outs

    def prepare_tx(self, tx_ins, tx_outs, tx_addr_ins, tx_addr_outs, op_return_data):
        for from_address, amount in tx_addr_ins.items():
            # Prepare the data for transaction
            utxos = self._fetch_utxo(from_address)
            vins = select_utxo(utxos, int(amount['amount'] + amount['fee']))
            if not vins:
                raise TransactionError(
                    _('insufficient funds in address %(address)s'),
                    code='invalid',
                    params={'address': from_address}
                )
                return
            change = balance_from_utxos(vins) - (amount['amount'] + amount['fee'])
            tx_ins += [utxo_to_txin(utxo) for utxo in vins]
            if change:
                tx_outs.append({'address': from_address,
                                'value': int(change * 10**8)})

        for to_address, amount in tx_addr_outs.items():
            tx_outs.append({'address': to_address,
                            'value': int(amount * 10**8)})

        if op_return_data:
            tx_outs.append({
                'script': mk_op_return_script(op_return_data.encode('utf8')),
                'value': 0
            })


class CreateRawTxView(CreateTx, View):

    @staticmethod
    def _fetch_utxo(address):
        utxo = get_rpc_connection().gettxoutaddress(address)
        return utxo

    def get(self, request, *args, **kwargs):
        form = RawTxForm(request.GET)
        if form.is_valid():
            # Fetch the data
            from_address = form.cleaned_data['from_address']
            to_address = form.cleaned_data['to_address']
            amount = form.cleaned_data['amount']
            fee = form.cleaned_data['fee']
            op_return_data = form.cleaned_data['op_return_data']
            tx_addr_in = {from_address: {'amount': amount, 'fee': fee}}
            tx_addr_out = {to_address: amount}

            ins = []
            outs = []
            try:
                self.prepare_tx(ins, outs, tx_addr_in, tx_addr_out, op_return_data)
            except TransactionError as e:
                return JsonResponse({'error': unicode(e.message) % e.params}, status=httplib.BAD_REQUEST)
            except:
                return JsonResponse({'error': 'invalid data'}, status=httplib.BAD_REQUEST)

            # Create the transaction
            raw_tx = make_raw_tx(ins, outs)

            return JsonResponse({'raw_tx': raw_tx})
        else:
            errors = ', '.join(reduce(lambda x, y: x + y, form.errors.values()))
            response = {'error': errors}
            return JsonResponse(response, status=httplib.BAD_REQUEST)


class GeneralTxView(CsrfExemptMixin, CreateTx, View):

    http_method_names = ['post']

    @staticmethod
    def _fetch_utxo(address):
        utxo = get_rpc_connection().gettxoutaddress(address)
        return utxo

    @staticmethod
    def _validate_json_obj(json_obj):
        try:
            err_name = 'json'
            required_fields = {'tx_in', 'tx_out'}
            required_keys = {
                'tx_in': {'from_address', 'amount'},
                'tx_out': {'to_address', 'amount'},
            }
            json_validator(json_obj, required_fields)
            # Validation of input
            err_name = 'tx_in'
            for tx_in in json_obj['tx_in']:
                json_validator(tx_in, required_keys['tx_in'])
                address_validator(tx_in['from_address'])
                tx_in['amount'] = Decimal(tx_in['amount'])
                amount_validator(tx_in['amount'], min_value=0, max_value=10**10, decimal_places=8)
                tx_in['fee'] = Decimal(tx_in['fee'])
                amount_validator(tx_in['fee'], min_value=0, max_value=10**10, decimal_places=8)
            # Validation of output
            err_name = 'tx_out'
            for tx_out in json_obj['tx_out']:
                json_validator(tx_out, required_keys['tx_out'])
                address_validator(tx_out['to_address'])
                tx_out['amount'] = Decimal(tx_out['amount'])
                amount_validator(tx_out['amount'], min_value=0, max_value=10**10, decimal_places=8)
        except TransactionError as e:
            e.params['name'] = err_name
            raise e

    def post(self, request, *args, **kwargs):
        try:
            json_obj = json.loads(request.body, parse_int=Decimal, parse_float=Decimal)
            self._validate_json_obj(json_obj)
        except TransactionError as e:
            return JsonResponse({'error': unicode(e.message) % e.params}, status=httplib.BAD_REQUEST)

        # Fetch the data
        op_return_data = json_obj['op_return_data'] if 'op_return_data' in json_obj else None
        tx_addr_ins = self._aggregate_inputs(json_obj['tx_in'])
        tx_addr_outs = self._aggregate_outputs(json_obj['tx_out'])

        tx_ins = []
        tx_outs = []

        try:
            self.prepare_tx(tx_ins, tx_outs, tx_addr_ins, tx_addr_outs, op_return_data)
        except TransactionError as e:
            return JsonResponse({'error': unicode(e.message) % e.params}, status=httplib.BAD_REQUEST)
        except:
            return JsonResponse({'error': 'invalid data'}, status=httplib.BAD_REQUEST)

        # Create the transaction
        raw_tx = make_raw_tx(tx_ins, tx_outs)

        return JsonResponse({'raw_tx': raw_tx})


class SendRawTxView(CsrfExemptMixin, View):

    def post(self, request, *args, **kwargs):
        raw_tx = request.POST.get('raw_tx', '')
        try:
            tx_id = get_rpc_connection().sendrawtransaction(raw_tx)
            response = {'tx_id': tx_id}
            return JsonResponse(response)
        except:
            logger.error('Invalid transaction: %s', raw_tx, exc_info=True)
            response = {'error': 'invalid raw transaction'}
            return JsonResponse(response, status=httplib.BAD_REQUEST)


class GetBalanceView(View):

    def get(self, request, address, *args, **kwargs):
        if request.GET.get('confirmed') == '1':
            utxos = get_rpc_connection().gettxoutaddress(address, mempool=False)
        else:
            utxos = get_rpc_connection().gettxoutaddress(address)
        balance = balance_from_utxos(utxos)
        return JsonResponse({'balance': balance})


class UtxoView(View):

    def get(self, request, address, *args, **kwargs):
        utxos = get_rpc_connection().gettxoutaddress(address)
        return JsonResponse(utxos, safe=False)
