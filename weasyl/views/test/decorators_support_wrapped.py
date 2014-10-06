from pyramid.view import view_config

from weasyl.views import decorators


def create_wrapped():
    """
    Create a twice-wrapped function for some tests.

    This is done in the function scope instead of the module scope because
    'base_func' and 'wrapped_once' must not leak into the module scope.
    """
    @view_config(name='base', renderer='string')
    def base_func(request):
        return 'base'

    @view_config(name='once', renderer='string')
    @decorators.wraps_respecting_view_config(base_func)
    def wrapped_once(request):
        return 'once'

    @view_config(name='twice', renderer='string')
    @decorators.wraps_respecting_view_config(wrapped_once)
    def wrapped_twice(request):
        return 'twice'

    return wrapped_twice


wrapped = create_wrapped()
