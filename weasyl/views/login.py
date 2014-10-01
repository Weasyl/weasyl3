import logging

import arrow
import colander as c
import deform.widget as w
from pyramid_deform import CSRFSchema
from pyramid.security import remember, forget
from pyramid.view import view_config
from pyramid import httpexceptions

from libweasyl.exceptions import LoginFailed
from ..login import try_login
from ..resources import RootResource
from .forms import Form, FormView, User


log = logging.getLogger(__name__)


class Signin(CSRFSchema):
    user = c.SchemaNode(User(), description='Username')
    password = c.SchemaNode(c.String(), description='Password', widget=w.PasswordWidget())

    def validator(self, form, values):
        try:
            try_login(**values)
        except LoginFailed as e:
            raise c.Invalid(form, e.args[0]) from e


@view_config(name='signin', context=RootResource, renderer='login/signin.jinja2', permission='signin', api='false')
class SigninView(FormView):
    schema = Signin()
    buttons = 'signin',

    def signin_success(self, appstruct):
        return httpexceptions.HTTPSeeOther(
            '/', headers=remember(self.request, appstruct['user'].userid))


@view_config(name='signout', context=RootResource, renderer='login/signout.jinja2', permission='signout', api='false')
class SignoutView(FormView):
    schema = CSRFSchema()
    buttons = 'signout',

    def signout_success(self, appstruct):
        return httpexceptions.HTTPSeeOther('/', headers=forget(self.request))


@c.deferred
def years_widget(node, kw):
    year = arrow.get().year
    return w.SelectWidget(values=[(str(y), str(y)) for y in range(year - 13, year - 113, -1)])


months_widget = w.SelectWidget(values=[(str(y), str(y)) for y in range(1, 13)])
days_widget = w.SelectWidget(values=[(str(y), str(y)) for y in range(1, 32)])


class Register(CSRFSchema):
    username = c.SchemaNode(
        c.String(), description='Desired username', error_name='Username')
    password = c.SchemaNode(
        c.String(), description='Password', widget=w.PasswordWidget())
    password_confirm = c.SchemaNode(
        c.String(), description='Confirm password', error_name='Password confirmation',
        widget=w.PasswordWidget())
    email = c.SchemaNode(c.String(), description='E-mail address')
    year_born = c.SchemaNode(c.Int(), error_name='Year', widget=years_widget)
    month_born = c.SchemaNode(c.Int(), error_name='Month', widget=months_widget)
    day_born = c.SchemaNode(
        c.Int(), description='', error_name='Day',
        widget=days_widget)


@view_config(name='register', context=RootResource, renderer='login/register.jinja2', permission='signin', api='false')
class RegisterView(FormView):
    schema = Register()
    buttons = 'register',

    def register_success(self, appstruct):
        return httpexceptions.HTTPSeeOther('/')


def login_forms(request):
    return {
        'signin': Form(Signin().bind(request=request)),
        'signout': Form(CSRFSchema().bind(request=request)),
    }
