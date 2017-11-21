from decimal import Decimal
import httplib
import json

from django.db.models import Max, Q
from django.http import JsonResponse
from django.views.generic import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.exceptions import ValidationError

from gcoin import make_raw_tx, mk_op_return_script
from oss_server.utils import address_validator
from .forms import GetAddressTxsForm, GetBlocksForm
from ..models import *
from ..pagination import *
from base.utils import balance_from_utxos, select_utxo, utxo_to_txin
from base.v1.forms import RawTxForm


class GetBlocksView(View):
    def get(self, request):
        form = GetBlocksForm(request.GET)
        if form.is_valid():
            starting_after = form.cleaned_data['starting_after']
            since = form.cleaned_data['since']
            until = form.cleaned_data['until']
            page_size = form.cleaned_data['page_size'] or 50

            block_list = Block.objects.filter(in_longest=1)

            if since is not None:
                block_list = block_list.filter(time__gte=since)

            if until is not None:
                block_list = block_list.filter(time__lt=until)

            is_first_page = False

            try:
                if starting_after:
                    start_block = Block.objects.get(hash=starting_after)
                else:
                    start_block = Block.objects.latest('height')
            except Tx.DoesNotExist:
                response = {'error': 'block not exist'}
                return JsonResponse(response, status=httplib.NOT_FOUND)

            max_height = Block.objects.all().aggregate(Max('height'))['height__max']
            pre_start_height = min(self._get_prev_start_height(start_block, page_size),
                                   max_height)

            if start_block and start_block.height == max_height:
                is_first_page = True
                start_block = None

            page, blocks = object_pagination(block_list, start_block, page_size)

            if len(blocks) > 0 and blocks.has_next():
                query_dict = request.GET.copy()
                query_dict['starting_after'] = blocks[-1].hash
                page['next_uri'] = '/explorer/v1/blocks?' + query_dict.urlencode()

            if len(blocks) > 0:
                if is_first_page:
                    page['prev_uri'] = ''
                else:
                    prev_dict = request.GET.copy()
                    prev_dict['starting_after'] = Block.objects.get(in_longest=1, height=pre_start_height)
                    page['prev_uri'] = '/explorer/v1/blocks?' + prev_dict.urlencode()

            response = {
                'page': page,
                'blocks': [block.as_dict() for block in blocks]
            }
            return JsonResponse(response)
        else:
            errors = ', '.join(reduce(lambda x, y: x + y, form.errors.values()))
            response = {'error': errors}
            return JsonResponse(response, status=httplib.BAD_REQUEST)

    def _get_prev_start_height(self, start_block, page_size):
        pre_start_height = start_block.height + page_size
        return pre_start_height


class GetBlockByHashView(View):
    def get(self, request, block_hash):
        try:
            response = {'block': Block.objects.get(hash=block_hash).as_dict()}
            return JsonResponse(response)
        except Block.DoesNotExist:
            response = {'error': 'block not exist'}
            return JsonResponse(response, status=httplib.NOT_FOUND)


class GetBlockByHeightView(View):
    def get(self, request, block_height):
        try:
            response = {'block': Block.objects.get(height=block_height, in_longest=1).as_dict()}
            return JsonResponse(response)
        except Block.DoesNotExist:
            response = {'error': 'block not exist'}
            return JsonResponse(response, status=httplib.NOT_FOUND)


class GetTxByHashView(View):
    def get(self, request, tx_hash):
        try:
            response = {'tx': Tx.objects.get(hash=tx_hash, block__in_longest=1).as_dict()}
            return JsonResponse(response)
        except Tx.DoesNotExist:
            response = {'error': 'tx not exist'}
            return JsonResponse(response, status=httplib.NOT_FOUND)


class GetAddressTxsView(View):
    def get(self, request, address):
        form = GetAddressTxsForm(request.GET)
        if form.is_valid():
            starting_after = form.cleaned_data['starting_after']
            since = form.cleaned_data['since']
            until = form.cleaned_data['until']
            page_size = form.cleaned_data['page_size'] or 50

            # tx should be in main chain, and distinct() prevents duplicate object
            Q1 = Q(tx_in__txout__address__address=address)
            Q2 = Q(tx_out__address__address=address)
            tx_list = Tx.objects.filter(Q1 | Q2, block__in_longest=1).distinct()

            if since is not None:
                tx_list = tx_list.filter(time__gte=since)

            if until is not None:
                tx_list = tx_list.filter(time__lt=until)

            try:
                start_tx = Tx.objects.get(hash=starting_after) if starting_after else None
            except Tx.DoesNotExist:
                response = {'error': 'tx not exist'}
                return JsonResponse(response, status=httplib.NOT_FOUND)

            page, txs = object_pagination(tx_list, start_tx, page_size)

            if len(txs) > 0 and txs.has_next():
                query_dict = request.GET.copy()
                query_dict['starting_after'] = txs[-1].hash
                page['next_uri'] = '/explorer/v1/transactions/address/' + address + '?' + query_dict.urlencode()

            response = {
                'page': page,
                'txs': [tx.as_dict() for tx in txs]
            }
            return JsonResponse(response)
        else:
            errors = ', '.join(reduce(lambda x, y: x + y, form.errors.values()))
            response = {'error': errors}
            return JsonResponse(response, status=httplib.BAD_REQUEST)


class GetAddressBalanceView(View):
    def get(self, request, address):
        utxo_list = TxOut.objects.filter(tx__block__in_longest=1,
                                         address__address=address,
                                         spent=0)

        balance = 0;
        for utxo in utxo_list:
            value = utxo.value
            balance += value
        return JsonResponse({'balance' : balance})


class GetAddressUtxoView(View):
    def get(self, request, address):
        utxo_list = TxOut.objects.filter(tx__block__in_longest=1,
                                         address__address=address,
                                         spent=0)

        response = {'utxo': [utxo.utxo_dict() for utxo in utxo_list]}
        return JsonResponse(response)


class GetAddressOpReturnView(View):
    def get(self, request, address):
        # choose all tx outs if other tx outs in the same tx are related to this address
        tx_out_list = TxOut.objects.filter(tx__tx_out__address__address=address)
        op_return_out = [out.op_return_dict() for out in tx_out_list if out.is_op_return]

        response = {'txout': op_return_out}
        return JsonResponse(response)


class CsrfExemptMixin(object):
    """
    Exempts the view from CSRF requirements.

    This should be the left-most mixin of a view.
    """
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(CsrfExemptMixin, self).dispatch(*args, **kwargs)


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
            utxo_list = TxOut.objects.filter(tx__block__in_longest=1,
                                             address__address=from_address,
                                             spent=0)
            utxos = [utxo.utxo_as_vin_dict() for utxo in utxo_list]
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
            utxos = TxOut.objects.filter(tx__block__in_longest=1,
                                         address__address=fee_address,
                                         spent=0)
            utxos = [utxo.utxo_as_vin_dict() for utxo in utxo_list]
            vins = select_utxo(utxos=utxos, sum=amount)
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

            raw_tx = make_raw_tx(tx_vins, tx_vouts)
        else:
            raw_tx = make_raw_tx(tx_vins, tx_vouts)

        return JsonResponse({'raw_tx': raw_tx})


class CreateRawTxView(View):

    def get(self, request, *args, **kwargs):
        form = RawTxForm(request.GET)
        if form.is_valid():
            from_address = form.cleaned_data['from_address']
            to_address = form.cleaned_data['to_address']
            amount = form.cleaned_data['amount']
            op_return_data = form.cleaned_data['op_return_data']

            utxo_list = TxOut.objects.filter(tx__block__in_longest=1,
                                             address__address=from_address,
                                             spent=0)
            utxos = [utxo.utxo_as_vin_dict() for utxo in utxo_list]
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
                raw_tx = make_raw_tx(ins, outs)
            else:
                raw_tx = make_raw_tx(ins, outs)

            return JsonResponse({'raw_tx': raw_tx})
        else:
            errors = ', '.join(reduce(lambda x, y: x + y, form.errors.values()))
            response = {'error': errors}
            return JsonResponse(response, status=httplib.BAD_REQUEST)
