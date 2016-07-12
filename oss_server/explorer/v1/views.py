import httplib

from django.http import JsonResponse
from django.views.generic import View

from ..models import *


class RetrieveBlockView(View):
    def get(self, request):
        if 'hash' in request.GET:
            return self.get_block_by_hash(request.GET['hash'])
        elif 'height' in request.GET:
            return self.get_block_by_height(request.GET['height'])
        else:
            return self.get_latest_blocks()

    def get_block_by_hash(self, hash):
        try:
            response = {'block': Block.objects.get(hash=hash).as_dict()}
            return JsonResponse(response)
        except Block.DoesNotExist:
            response = {'error': 'block not exist'}
            return JsonResponse(response, status=httplib.NOT_FOUND)

    def get_block_by_height(self, height):
        try:
            response = {'block': Block.objects.get(height=height, in_longest=1).as_dict()}
            return JsonResponse(response)
        except Block.DoesNotExist:
            response = {'error': 'block not exist'}
            return JsonResponse(response, status=httplib.NOT_FOUND)

    def get_latest_blocks(self):
        latest_blocks = Block.objects.filter(in_longest=1)[:50]
        response = {'blocks': [block.as_dict() for block in latest_blocks]}
        return JsonResponse(response)
