import logging

import colander as c
import deform.widget as w
from pyramid_deform import CSRFSchema
from pyramid.security import remember, forget
from pyramid.view import view_config
from pyramid import httpexceptions

from ..login import try_login
from ..resources import RootResource
from .forms import FormView


log = logging.getLogger(__name__)


class Signin(CSRFSchema):
    username = c.SchemaNode(c.String(), description='Username or e-mail')
    password = c.SchemaNode(c.String(), description='Password', widget=w.PasswordWidget())


@view_config(name='signin', context=RootResource, renderer='signin.jinja2', permission='signin')
class SigninView(FormView):
    schema = Signin()
    buttons = 'signin',

    def signin_success(self, appstruct):
        del appstruct['csrf_token']
        userid = try_login(**appstruct)
        return httpexceptions.HTTPSeeOther(
            '/', headers=remember(self.request, userid))


@view_config(name='signout', context=RootResource, renderer='signout.jinja2', permission='signout')
class SignoutView(FormView):
    schema = CSRFSchema()
    buttons = 'signout',

    def signout_success(self, appstruct):
        return httpexceptions.HTTPSeeOther('/', headers=forget(self.request))
