import colander as c
from pyramid.view import view_config

from weasyl.views import forms


class FormA(c.Schema):
    a = c.SchemaNode(c.Int())


class FormB(c.Schema):
    b = c.SchemaNode(c.Int())


def a_success(context, request, appstruct):
    return {'a_success': appstruct}


def b_success(context, request, appstruct):
    return {'b_success': appstruct}


@view_config(name='form-view', renderer='json', request_method='GET')
@forms.form_renderer(FormA, 'a', success=a_success, button='a_button', name='form-a', renderer='json')
@forms.form_renderer(FormB, 'b', success=b_success, button='b_button', name='form-b', renderer='json')
def form_view(context, request, forms=()):
    return forms
