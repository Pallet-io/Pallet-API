import httplib

from django.core.paginator import EmptyPage
from django.http import JsonResponse
from django.views.generic import View

from infinite_scroll_pagination.paginator import SeekPaginator

from ..models import *


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

        pk = None
        time = None
        if starting_after:
            try:
                tx = Tx.objects.get(hash=starting_after)
                pk = tx.pk
                time = tx.time
            except Tx.DoesNotExist:
                response = {'error': 'tx not exist'}
                return JsonResponse(response, status=httplib.NOT_FOUND)

        # tx should be NORMAL / MINT type and should be in main chain, and distinct() prevents duplicate object
        tx_list = Tx.objects.filter(tx_out__color=color_id, type__lte=1, block__in_longest=1).distinct()

        paginator = SeekPaginator(tx_list, per_page=50, lookup_field='time')
        try:
            txs = paginator.page(value=time, pk=pk)
            page = {
                'starting_after': txs[0].hash if txs else None,
                'ending_before': txs[-1].hash if txs else None
            }

            if txs.has_next():
                page['next_uri'] = '/explorer/v1/transactions/color/' + color_id + '?starting_after=' + txs[-1].hash
            else:
                page['next_uri'] = None
        except EmptyPage:
            txs = []
            page = {
                'starting_after': None,
                'ending_before': None,
                'next_uri': None
            }

        response = {
            'page': page,
            'txs': [tx.as_dict() for tx in txs]
        }
        return JsonResponse(response)
