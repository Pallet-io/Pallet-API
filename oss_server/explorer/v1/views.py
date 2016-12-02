import httplib

from django.db.models import Q
from django.http import JsonResponse
from django.views.generic import View

from ..models import *
from ..pagination import *


class GetLatestBlocksView(View):
    def get(self, request):
        latest_blocks = Block.objects.filter(in_longest=1)[:50]
        response = {'blocks': [block.as_dict() for block in latest_blocks]}
        return JsonResponse(response)


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


class GetColorTxsView(View):
    def get(self, request, color_id):
        starting_after = request.GET.get('starting_after', None)
        page_size = request.GET.get('page_size', 50)

        # tx should be NORMAL / MINT type and in main chain, and distinct() prevents duplicate object
        Q1 = Q(tx_in__txout__color=color_id)
        Q2 = Q(tx_out__color=color_id)
        tx_list = Tx.objects.filter(Q1 | Q2, type__lte=1, block__in_longest=1).distinct()

        try:
            page, txs = tx_pagination(tx_list, starting_after, int(page_size))
        except Tx.DoesNotExist:
            response = {'error': 'tx not exist'}
            return JsonResponse(response, status=httplib.NOT_FOUND)

        if len(txs) > 0 and txs.has_next():
            query_dict = request.GET.copy()
            query_dict['starting_after'] = txs[-1].hash
            page['next_uri'] = '/explorer/v1/transactions/color/' + color_id + '?' + query_dict.urlencode()

        response = {
            'page': page,
            'txs': [tx.as_dict() for tx in txs]
        }
        return JsonResponse(response)


class GetAddressTxsView(View):
    def get(self, request, address):
        starting_after = request.GET.get('starting_after', None)
        tx_type = request.GET.get('tx_type', None)
        since = request.GET.get('since', None)
        until = request.GET.get('until', None)
        page_size = request.GET.get('page_size', 50)

        # tx should be in main chain, and distinct() prevents duplicate object
        Q1 = Q(tx_in__txout__address__address=address)
        Q2 = Q(tx_out__address__address=address)
        tx_list = Tx.objects.filter(Q1 | Q2, block__in_longest=1).distinct()

        if tx_type:
            tx_list = tx_list.filter(type=tx_type)

        if since:
            tx_list = tx_list.filter(time__gte=since)

        if until:
            tx_list = tx_list.filter(time__lte=until)

        try:
            page, txs = tx_pagination(tx_list, starting_after, int(page_size))
        except Tx.DoesNotExist:
            response = {'error': 'tx not exist'}
            return JsonResponse(response, status=httplib.NOT_FOUND)

        if len(txs) > 0 and txs.has_next():
            query_dict = request.GET.copy()
            query_dict['starting_after'] = txs[-1].hash
            page['next_uri'] = '/explorer/v1/transactions/address/' + address + '?' + query_dict.urlencode()

        response = {
            'page': page,
            'txs': [tx.as_dict() for tx in txs]
        }
        return JsonResponse(response)


class GetAddressBalanceView(View):
    def get(self, request, address):
        utxo_list = TxOut.objects.filter(address__address=address, spent=0)

        response = {}
        for utxo in utxo_list:
            color = int(utxo.color)
            value = utxo.value
            response[color] = response.get(color, 0) + value
        return JsonResponse(response)


class GetAddressUtxoView(View):
    def get(self, request, address):
        utxo_list = TxOut.objects.filter(address__address=address, spent=0)

        response = {'utxo': [utxo.utxo_dict() for utxo in utxo_list]}
        return JsonResponse(response)


class GetAddressOpReturnView(View):
    def get(self, request, address):
        # choose all tx outs if other tx outs in the same tx are related to this address
        tx_out_list = TxOut.objects.filter(tx__tx_out__address__address=address, tx__type=5)
        op_return_out = [out.op_return_dict() for out in tx_out_list if out.is_op_return]

        response = {'txout': op_return_out}
        return JsonResponse(response)
