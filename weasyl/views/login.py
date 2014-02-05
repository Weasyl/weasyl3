import logging

import colander as c
import deform.widget as w
from pyramid_deform import CSRFSchema
from pyramid.security import remember, forget
from pyramid.view import view_config
from pyramid import httpexceptions

from ..login import try_login
from .forms import FormView


log = logging.getLogger(__name__)


class Login(CSRFSchema):
    username = c.SchemaNode(c.String(), description='Username or e-mail')
    password = c.SchemaNode(c.String(), description='Password', widget=w.PasswordWidget())


@view_config(route_name='signin', renderer='signin.jinja2', permission='signin')
class LoginView(FormView):
    schema = Login()
    buttons = 'signin',

    def signin_success(self, appstruct):
        del appstruct['csrf_token']
        userid = try_login(**appstruct)
        return httpexceptions.HTTPSeeOther(
            '/', headers=remember(self.request, userid))


@view_config(route_name='signout', renderer='signout.jinja2', permission='signout')
class LogoutView(FormView):
    schema = CSRFSchema()
    buttons = 'signout',

    def signout_success(self, appstruct):
        return httpexceptions.HTTPSeeOther('/', headers=forget(self.request))
