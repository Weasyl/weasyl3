from pyramid.view import view_config

from libweasyl.exceptions import ExpectedWeasylError
from ..resources import DebugResource


@view_config(name='expected-exception', context=DebugResource)
def expected_exception(request):
    raise ExpectedWeasylError('this error was expected')


@view_config(name='unexpected-exception', context=DebugResource)
def unexpected_exception(request):
    raise RuntimeError('this error was not expected')
