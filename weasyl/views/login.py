import logging

import colander as c
import deform.widget as w
from pyramid_deform import CSRFSchema
from pyramid.view import view_config
from pyramid import httpexceptions

from ..login import try_login
from .forms import FormView


log = logging.getLogger(__name__)


class Login(CSRFSchema):
    username = c.SchemaNode(c.String(), description='Username or e-mail')
    password = c.SchemaNode(c.String(), description='Password', widget=w.PasswordWidget())


@view_config(route_name='signin', renderer='signin.jinja2')
class LoginView(FormView):
    schema = Login()
    buttons = 'login',

    def login_success(self, appstruct):
        del appstruct['csrf_token']
        try_login(self.request, **appstruct)
        return httpexceptions.HTTPSeeOther('/')
