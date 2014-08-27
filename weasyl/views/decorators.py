import functools

from decorator import decorator
from pyramid.renderers import render_to_response
from pyramid.view import view_config


@decorator
def requires_no_login(f, request):
    if request.session['userid']:
        return render_to_response(
            'errors/generic.jinja2', {'message': 'You must be signed out.'})
    return f(request)


def also_api_view(*, template, **view_args):
    def deco(func):
        @view_config(_depth=1, renderer=template, api='false', **view_args)
        @view_config(_depth=1, renderer='json', api='true', **view_args)
        @functools.wraps(func)
        def wrapper(*a, **kw):
            return func(*a, **kw)

        return wrapper
    return deco
