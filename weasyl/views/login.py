import logging

import colander as c
from deform.form import Form
import deform.widget as w
from pyramid_deform import CSRFSchema
from pyramid.security import remember, forget
from pyramid.view import view_config
from pyramid import httpexceptions

from ..login import LoginFailed, try_login
from ..resources import RootResource
from .forms import FormView, User


log = logging.getLogger(__name__)


class Signin(CSRFSchema):
    user = c.SchemaNode(User(), description='Username')
    password = c.SchemaNode(c.String(), description='Password', widget=w.PasswordWidget())


def login_form_validator(node, value):
    try:
        try_login(**value)
    except LoginFailed as e:
        raise c.Invalid(node, e.args[0]) from e


@view_config(name='signin', context=RootResource, renderer='login/signin.jinja2', permission='signin')
class SigninView(FormView):
    schema = Signin(validator=login_form_validator)
    buttons = 'signin',

    def signin_success(self, appstruct):
        return httpexceptions.HTTPSeeOther(
            '/', headers=remember(self.request, appstruct['user'].userid))


@view_config(name='signout', context=RootResource, renderer='login/signout.jinja2', permission='signout')
class SignoutView(FormView):
    schema = CSRFSchema()
    buttons = 'signout',

    def signout_success(self, appstruct):
        return httpexceptions.HTTPSeeOther('/', headers=forget(self.request))


def login_forms(request):
    return {
        'signin': Form(Signin().bind(request=request)),
        'signout': Form(CSRFSchema().bind(request=request)),
    }
