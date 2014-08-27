from urllib.parse import urljoin


def minimize_media(request, obj):
    if obj is None:
        return None
    base_url = request.resource_url(None)
    return {
        k: [
            {
                'mediaid': v['mediaid'],
                'url': urljoin(base_url, v['display_url']),
                'links': minimize_media(request, v['described']),
            } for v in vs]
        for k, vs in obj.items()}
