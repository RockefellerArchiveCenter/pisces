from django.http import JsonResponse
from django.urls import reverse

from elasticsearch import NotFoundError


def document_or_404(cls, identifier):
    try:
        s = cls.get(id=identifier)
        return JsonResponse(s.to_dict())
    except NotFoundError:
        return JsonResponse({"detail": "Not found"}, status=404)


def documents_of_type(cls, key):
    s = cls().search().query('match_all')
    resp = s.execute()
    data = []
    for hit in resp:
        # TODO: some formatting here which returns the object we want
        c = hit.to_dict()
        c.update({'uri': reverse('api:{}-detail'.format(key), kwargs={'id': hit.meta.id})})
        data.append(c)
    return JsonResponse({'{}s'.format(key): data})
