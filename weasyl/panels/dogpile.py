import time

from dogpile.cache.proxy import ProxyBackend
from pyramid.threadlocal import get_current_request
from pyramid_debugtoolbar.panels import DebugPanel


def build_wrapper(name):
    def wrapper(self, *args):
        proxied_method = getattr(self.proxied, name)
        request = get_current_request()
        if request is None or not hasattr(request, 'pdtb_dogpile_queries'):
            return proxied_method(*args)
        start = time.time()
        ret = proxied_method(*args)
        delta = time.time() - start
        request.pdtb_dogpile_queries.append({
            'method': name,
            'arguments': args,
            'duration': delta * 1000,
        })
        return ret

    return wrapper


class RequestLoggingProxy(ProxyBackend):
    for name in ['get', 'get_multi', 'set', 'set_multi', 'delete', 'delete_multi']:
        locals()[name] = build_wrapper(name)


class DogpileDebugPanel(DebugPanel):
    name = 'Dogpile'
    title = 'Dogpile Queries'
    nav_title = 'Dogpile'
    template = 'weasyl.panels:templates/dogpile.dbtmako'

    def __init__(self, request):
        request.pdtb_dogpile_queries = self.queries = []
        self.data = {'queries': self.queries}

    @property
    def has_content(self):
        return bool(self.queries)

    @property
    def nav_subtitle(self):
        if self.queries:
            return str(len(self.queries))


def includeme(config):
    settings = config.registry.settings
    settings['debugtoolbar.panels'].append(DogpileDebugPanel)
    region = settings[settings['debugtoolbar.dogpile.region_key']]
    region.wrap(RequestLoggingProxy)
