import functools

from decorator import decorator
from pyramid.renderers import render_to_response
from pyramid.view import view_config


def also_api_view(*, template, **view_args):
    def deco(func):
        @view_config(_depth=1, renderer=template, api='false', **view_args)
        @view_config(_depth=1, renderer='json', api='true', **view_args)
        @functools.wraps(func)
        def wrapper(*a, **kw):
            return func(*a, **kw)

        return wrapper
    return deco
