from decimal import Decimal
import httplib
import json
import logging

from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from gcoin import (encode_license, make_mint_raw_tx, make_raw_tx,
                   mk_op_return_script)
from gcoinrpc import connect_to_remote
from gcoinrpc.exceptions import InvalidAddressOrKey, InvalidParameter

from oss_server.types import TransactionType
from oss_server.utils import address_validator

from ..utils import balance_from_utxos, select_utxo, utxo_to_txin
from .forms import (CreateSmartContractRawTxForm, RawTxForm)

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

class CreateSmartContractRawTxView(CsrfExemptMixin, View):
    TX_FEE = 1
    DEFAULT_CONTRACT_FEE = 1

    def post(self, request, *args, **kwargs):
        form = CreateSmartContractRawTxForm(request.POST)
        if form.is_valid():
            from_address = form.cleaned_data['from_address']
            to_address = form.cleaned_data['to_address']
            amount = form.cleaned_data['amount']
            code = form.cleaned_data['code']
            contract_fee = form.cleaned_data['contract_fee'] or self.DEFAULT_CONTRACT_FEE

            utxos = get_rpc_connection().gettxoutaddress(from_address)
            total_fee = contract_fee + self.TX_FEE

            if amount:
                inputs = select_utxo(utxos=utxos, sum= (amount + total_fee))
                if not inputs:
                    return JsonResponse({'error': 'insufficient funds'}, status=httplib.BAD_REQUEST)
            else:
                inputs = []

            ins = [utxo_to_txin(utxo) for utxo in inputs]

            outs = []
            if amount:
                outs.append({
                    'address': to_address,
                    'value': int(amount * (10**8)),
                })
                change = balance_from_utxos(inputs) - amount - total_fee
                if change:
                    outs.append({
                        'address': from_address,
                        'value': int(change * (10**8)),
                    })

            raw_tx = make_raw_tx(ins, outs, TransactionType.to_number('CONTRACT'))
            return JsonResponse({'raw_tx': raw_tx})
        else:
            errors = ', '.join(reduce(lambda x, y: x + y, form.errors.values()))
            response = {'error': errors}
            return JsonResponse(response, status=httplib.BAD_REQUEST)

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


class CreateRawTxView(View):

    def get(self, request, *args, **kwargs):
        form = RawTxForm(request.GET)
        if form.is_valid():
            from_address = form.cleaned_data['from_address']
            to_address = form.cleaned_data['to_address']
            amount = form.cleaned_data['amount']
            op_return_data = form.cleaned_data['op_return_data']

            utxos = get_rpc_connection().gettxoutaddress(from_address)
            inputs = select_utxo(utxos, amount + 1)
            if not inputs:
                return JsonResponse({'error': 'insufficient funds'}, status=httplib.BAD_REQUEST)

            ins = [utxo_to_txin(utxo) for utxo in inputs]
            outs = [{'address': to_address, 'value': int(amount * 10**8)}]
            # Now for the `change` part.
            inputs_value = balance_from_utxos(inputs)
            change = inputs_value - amount - 1
            if change:
                outs.append({'address': from_address,
                             'value': int(change * 10**8)})

            if op_return_data:
                outs.append({
                    'script': mk_op_return_script(op_return_data.encode('utf8')),
                    'value': 0,
                })
                raw_tx = make_raw_tx(ins, outs, 5)  # contract type
            else:
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


class GeneralTxView(CsrfExemptMixin, View):
    http_method_names = ['post']

    @staticmethod
    def _validate_json_obj(json_obj):
        if len(json_obj['tx_info']) < 1:
            return '`tx_info` does not have any item'

        tx_info_key_set = {'from_address', 'to_address', 'amount'}
        for tx_info in json_obj['tx_info']:
            if not tx_info_key_set <= set(tx_info.keys()):
                return 'objects in `tx_info` should contain keys `from_address`, `to_address`, `amount`'
            try:
                address_validator(tx_info['from_address'])
            except ValidationError:
                return 'invalid address {}'.format(tx_info['from_address'])
            try:
                address_validator(tx_info['to_address'])
            except ValidationError:
                return 'invalid address {}'.format(tx_info['to_address'])
            tx_info['amount'] = Decimal(tx_info['amount'])

    @staticmethod
    def _aggregate_inputs(tx_info_list):
        tx_info_in = {}

        for tx_info in tx_info_list:
            from_address = tx_info['from_address']

            addr_in = tx_info_in.setdefault(from_address, 0)
            tx_info_in[from_address] += tx_info['amount']

        return tx_info_in

    @staticmethod
    def _aggregate_outputs(tx_info_list):
        tx_info_out = {}

        for tx_info in tx_info_list:
            to_address = tx_info['to_address']

            addr_in = tx_info_out.setdefault(to_address, 0)
            tx_info_out[to_address] += tx_info['amount']

        return tx_info_out

    def post(self, request, *args, **kwargs):
        try:
            json_obj = json.loads(request.body)
            error_msg = self._validate_json_obj(json_obj)
        except:
            return JsonResponse({'error': 'invalid data'}, status=httplib.BAD_REQUEST)
        else:
            if error_msg:
                return JsonResponse({'error': error_msg}, status=httplib.BAD_REQUEST)

        op_return_data = json_obj['op_return_data'] if 'op_return_data' in json_obj else None
        tx_info_ins = self._aggregate_inputs(json_obj['tx_info'])
        tx_info_outs = self._aggregate_outputs(json_obj['tx_info'])

        tx_vins = []
        tx_vouts = []
        fee_included = False
        fee_address = json_obj['tx_info'][0]['from_address']

        for from_address, amount in tx_info_ins.items():
            utxos = get_rpc_connection().gettxoutaddress(from_address)

            vins = select_utxo(utxos=utxos, sum=amount)
            if not vins:
                error_msg = 'insufficient amount in address {}'.format(from_address)
                return JsonResponse({'error': error_msg}, status=httplib.BAD_REQUEST)

            change = balance_from_utxos(vins) - amount

            if from_address == fee_address :
                vins = select_utxo(utxos=utxos, sum=amount+1)
                if not vins:
                    error_msg = 'insufficient fee in address {}'.format(from_address)
                    return JsonResponse({'error': error_msg}, status=httplib.BAD_REQUEST)
                fee_included = True
                change = balance_from_utxos(vins) - (amount + 1)

            tx_vins += [utxo_to_txin(utxo) for utxo in vins]

            if change:
                    tx_vouts.append({'address': from_address,
                                     'value': int(change * 10**8)})

        if not fee_included:
            utxos = get_rpc_connection().gettxoutaddress(fee_address)

            vins = select_utxo(utxos=utxos, sum=1)
            if not vins:
                error_msg = 'insufficient fee in address {}'.format(fee_address)
                return JsonResponse({'error': error_msg}, status=httplib.BAD_REQUEST)
            tx_vins += [utxo_to_txin(utxo) for utxo in vins]

            change = balance_from_utxos(vins)[1] - 1
            if change:
                tx_vouts.append({'address': fee_address,
                                 'value': int(change * 10**8)})

        for to_address, amount in tx_info_outs.items():
            tx_vouts.append({'address': to_address,
                             'value': int(amount * 10**8)})

        if op_return_data:
            tx_vouts.append({
                'script': mk_op_return_script(op_return_data.encode('utf8')),
                'value': 0
            })

            raw_tx = make_raw_tx(tx_vins, tx_vouts, TransactionType.to_number("CONTRACT"))
        else:
            raw_tx = make_raw_tx(tx_vins, tx_vouts)

        return JsonResponse({'raw_tx': raw_tx})
