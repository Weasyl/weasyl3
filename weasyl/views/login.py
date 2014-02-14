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
from .. import dates
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


@c.deferred
def years_widget(node, kw):
    year = dates.now().year
    return w.SelectWidget(values=[(str(y), str(y)) for y in range(year - 13, year - 113, -1)])


months_widget = w.SelectWidget(values=[(str(y), str(y)) for y in range(1, 13)])
days_widget = w.SelectWidget(values=[(str(y), str(y)) for y in range(1, 32)])


class Register(CSRFSchema):
    username = c.SchemaNode(c.String(), description='Desired username')
    password = c.SchemaNode(c.String(), description='Password', widget=w.PasswordWidget())
    password_confirm = c.SchemaNode(c.String(), description='Confirm password', widget=w.PasswordWidget())
    email = c.SchemaNode(c.String(), description='E-mail address')
    year_born = c.SchemaNode(c.Int(), widget=years_widget)
    month_born = c.SchemaNode(c.Int(), widget=months_widget)
    day_born = c.SchemaNode(c.Int(), description='Date of birth', widget=days_widget)


@view_config(name='register', context=RootResource, renderer='login/register.jinja2', permission='signin')
class RegisterView(FormView):
    schema = Register()
    buttons = 'register',

    def register_success(self, appstruct):
        return httpexceptions.HTTPSeeOther(
            '/', headers=remember(self.request, appstruct['user'].userid))


def login_forms(request):
    return {
        'signin': Form(Signin().bind(request=request)),
        'signout': Form(CSRFSchema().bind(request=request)),
    }
