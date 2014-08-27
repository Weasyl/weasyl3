import functools

from decorator import decorator
from pyramid.renderers import render_to_response
from pyramid.view import view_config
from venusian import Categories


def wraps_respecting_view_config(wrapped):
    def deco(wrapper):
        functools.update_wrapper(wrapper, wrapped)
        new_callbacks = Categories(wrapper)
        callbacks = getattr(wrapper, '__venusian_callbacks__', None)
        if callbacks is not None:
            new_callbacks.update(callbacks)
        wrapper.__venusian_callbacks__ = new_callbacks
        return wrapper
    return deco


def also_api_view(*, template, **view_args):
    def deco(func):
        @view_config(_depth=1, renderer=template, api='false', **view_args)
        @view_config(_depth=1, renderer='json', api='true', **view_args)
        @wraps_respecting_view_config(func)
        def wrapper(*a, **kw):
            return func(*a, **kw)

        return wrapper
    return deco
