from pyramid.config import Configurator
from pyramid.testing import DummyRequest
import pytest


def auth_policy_request(policy, **kwargs):
    config = Configurator(authentication_policy=policy, authorization_policy=policy)
    config.commit()
    ret = DummyRequest(**kwargs)
    # this is required because pyramid stupidly does ``self.__dict__.update``
    # instead of respecting descriptors when building DummyRequest.
    ret.registry = config.registry
    return ret


skip_functional = pytest.mark.skipif(
    pytest.config.getvalue('skip_functional'),
    reason='functional tests skipped')
