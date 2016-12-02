from django.core.paginator import EmptyPage

from infinite_scroll_pagination.paginator import SeekPaginator

from .models import Tx


def tx_pagination(tx_list, starting_after=None, per_page=50):
    pk = None
    time = None
    if starting_after:
        tx = Tx.objects.get(hash=starting_after)
        pk = tx.pk
        time = tx.time

    paginator = SeekPaginator(tx_list, per_page=per_page, lookup_field='time')
    try:
        txs = paginator.page(value=time, pk=pk)
        page = {
            'starting_after': txs[0].hash if txs else None,
            'ending_before': txs[-1].hash if txs else None,
            'next_uri': None
        }
    except EmptyPage:
        txs = []
        page = {
            'starting_after': None,
            'ending_before': None,
            'next_uri': None
        }

    return page, txs
