from django.core.paginator import EmptyPage

from infinite_scroll_pagination.paginator import SeekPaginator


def object_pagination(object_list, start_object=None, per_page=50):
    """
    Paginate a list of objects (e.g transactions or blocks). The `start_object` object should have attribute `pk` and
    `time`.

    :param object_list: A list of objects need to paginate
    :param start_object: Starting object
    :param per_page: The page size
    :return: (page, objects). page is the pagination info. objects is the queried objects.
    """
    pk = None
    time = None
    if start_object:
        pk = start_object.pk
        time = start_object.time

    paginator = SeekPaginator(object_list, per_page=per_page, lookup_field='time')
    try:
        objects = paginator.page(value=time, pk=pk)
        page = {
            'starting_after': objects[0].hash if objects else None,
            'ending_before': objects[-1].hash if objects else None,
            'next_uri': None
        }
    except EmptyPage:
        objects = []
        page = {
            'starting_after': None,
            'ending_before': None,
            'next_uri': None
        }

    return page, objects
