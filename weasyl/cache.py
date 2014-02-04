import re
import threading

import anyjson
from dogpile.cache.api import CachedValue, NO_VALUE
from dogpile.cache.proxy import ProxyBackend
from dogpile.cache import make_region


_bad_key_regexp = re.compile('[\x00-\x20\x7f]')


def escape_key(key):
    key = str(key)
    return _bad_key_regexp.sub('.', key)


def key_generator(namespace, func):
    prefix = '%s:%s:%s' % (namespace, func.__module__, func.__name__)

    def generate_key(*args):
        return '%s:%s' % (prefix, ':'.join(escape_key(x) for x in args))

    return generate_key


region = make_region(function_key_generator=key_generator)


class ThreadCacheProxy(ProxyBackend):
    _local = threading.local()

    @property
    def _dict(self):
        if not hasattr(self._local, 'cache_dict'):
            self._local.cache_dict = {}
        return self._local.cache_dict

    def get(self, key):
        d = self._dict
        if key in d:
            return d[key]
        ret = self.proxied.get(key)
        if ret is not NO_VALUE:
            d[key] = ret
        return ret

    def get_multi(self, keys):
        d = self._dict
        to_fetch = []
        ret = []
        for key in keys:
            ret.append(d.get(key, NO_VALUE))
            if ret[-1] is NO_VALUE:
                to_fetch.append((key, len(ret) - 1))
        if not to_fetch:
            return ret
        keys_to_fetch, indices = zip(*to_fetch)
        for key, index, value in zip(keys_to_fetch, indices, self.proxied.get_multi(keys_to_fetch)):
            if value is NO_VALUE:
                continue
            d[key] = ret[index] = value
        return ret

    def set(self, key, value):
        self._dict[key] = value
        self.proxied.set(key, value)

    def set_multi(self, pairs):
        self._dict.update(pairs)
        self.proxied.set_multi(pairs)

    def delete(self, key):
        self._dict.pop(key, None)
        self.proxied.delete(key)

    def delete_multi(self, keys):
        d = self._dict
        for key in keys:
            d.pop(key, None)
        self.proxied.delete_multi(keys)


class JSONProxy(ProxyBackend):
    def load(self, value):
        if value is NO_VALUE:
            return NO_VALUE
        payload, metadata = anyjson.loads(value)
        metadata['ct'] = float(metadata['ct'])
        return CachedValue(payload, metadata)

    def get(self, key):
        return self.load(self.proxied.get(key))

    def get_multi(self, keys):
        return map(self.load, self.proxied.get_multi(keys))

    def save(self, value):
        ret = [value.payload, value.metadata.copy()]
        # turn this into a string because yajl will try to represent this in
        # scientific notation, losing precision.
        ret[1]['ct'] = '%0.6f' % ret[1]['ct']
        return anyjson.dumps(ret)

    def set(self, key, value):
        self.proxied.set(key, self.save(value))

    def set_multi(self, pairs):
        self.proxied.set_multi({k: self.save(v) for k, v in pairs.items()})
