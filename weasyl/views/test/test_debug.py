import pytest

from libweasyl.exceptions import ExpectedWeasylError
from weasyl.views import debug


def test_expected_exception():
    """
    expected_exception just raises an ExpectedWeasylError always.
    """
    pytest.raises(ExpectedWeasylError, debug.expected_exception, None)


def test_unexpected_exception():
    """
    unexpected_exception just raises a RuntimeError always.
    """
    pytest.raises(RuntimeError, debug.unexpected_exception, None)
