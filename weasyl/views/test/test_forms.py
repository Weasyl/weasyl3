import colander as c
import deform
from pyramid.config import Configurator
from pyramid.renderers import JSON
from pyramid.view import view_config
import pytest
import webtest

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


def field_serializer(field, request):
    return {
        'name': field.name,
        'children': field.children,
        'cstruct': field.cstruct,
    }


def schema_node_serializer(node, request):
    return {
        'name': node.name,
    }


@pytest.fixture(scope='module')
def testapp():
    config = Configurator()
    config.scan()

    json_renderer = JSON()
    json_renderer.add_adapter(deform.Field, field_serializer)
    json_renderer.add_adapter(c.SchemaNode, schema_node_serializer)
    json_renderer.add_adapter(type(c.null), lambda ign1, ign2: None)
    config.add_renderer('json', json_renderer)

    return webtest.TestApp(config.make_wsgi_app())


def test_form_renderer_multiple_forms_appear(testapp):
    """
    If ``form_renderer`` is applied multiple times to a function, the view will
    receive multiple forms in its ``forms`` argument.
    """
    j = testapp.get('/form-view').json
    assert j['_a_form']
    assert j['_a_errors'] is None
    assert j['_b_form']
    assert j['_b_errors'] is None


def test_form_renderer_no_post_to_base_route(testapp):
    """
    XXX: why is this test useful?
    """
    resp = testapp.post('/form-view', {'a': '1', 'a_button': 'yes'}, expect_errors=True)
    assert resp.status_int == 404


def test_form_renderer_error_on_first_form(testapp):
    """
    Submitting an invalid form to the first form declared gives back form
    errors for that form but also the unfilled other form.
    """
    j = testapp.post('/form-a', {'a': 'not-an-int', 'a_button': 'yes'}).json
    assert j['_a_form']
    assert j['_a_errors']
    assert j['_b_form']
    assert j['_b_errors'] is None


def test_form_renderer_error_on_second_form(testapp):
    """
    Submitting an invalid form to the second form declared gives back form
    errors for that form but also the unfilled other form.
    """
    j = testapp.post('/form-b', {'b': 'not-an-int', 'b_button': 'yes'}).json
    assert j['_a_form']
    assert j['_a_errors'] is None
    assert j['_b_form']
    assert j['_b_errors']


def test_form_renderer_success_on_first_form(testapp):
    """
    Submitting a valid form to the first form declared triggers the success
    callback for the first form.
    """
    j = testapp.post('/form-a', {'a': '1', 'a_button': 'yes'}).json
    assert j == {'a_success': {'a': 1}}


def test_form_renderer_success_on_second_form(testapp):
    """
    Submitting a valid form to the second form declared triggers the success
    callback for the second form.
    """
    j = testapp.post('/form-b', {'b': '2', 'b_button': 'yes'}).json
    assert j == {'b_success': {'b': 2}}


def test_form_renderer_error_on_first_form_with_both_submitted(testapp):
    """
    If the data for both forms is contained in the POST request and the data is
    submitted to the endpoint for the first form, only the first form is
    validated. The other form is left unfilled.
    """
    j = testapp.post('/form-a', {
        'a': 'not-an-int', 'a_button': 'yes',
        'b': 'not-an-int', 'b_button': 'yes',
    }).json
    assert j['_a_form']
    assert j['_a_errors']
    assert j['_b_form']
    assert j['_b_errors'] is None


def test_form_renderer_error_on_second_form_with_both_submitted(testapp):
    """
    If the data for both forms is contained in the POST request and the data is
    submitted to the endpoint for the second form, only the second form is
    validated. The other form is left unfilled.
    """
    j = testapp.post('/form-b', {
        'a': 'not-an-int', 'a_button': 'yes',
        'b': 'not-an-int', 'b_button': 'yes',
    }).json
    assert j['_a_form']
    assert j['_a_errors'] is None
    assert j['_b_form']
    assert j['_b_errors']


@pytest.mark.parametrize('input_valid', [True, False])
@pytest.mark.parametrize(('endpoint', 'form'), [
    ('/form-a', 'b'),
    ('/form-b', 'a'),
])
def test_form_renderer_no_errors_on_posting_to_wrong_endpoint(testapp, input_valid, endpoint, form):
    """
    If the wrong form is submitted to an endpoint, it isn't validated, whether
    or not the input to the form was valid.
    """
    data = '1' if input_valid else 'not-an-int'
    j = testapp.post(endpoint, {form: data, form + '_button': 'yes'}).json
    assert j['_a_form']
    assert j['_a_errors'] is None
    assert j['_b_form']
    assert j['_b_errors'] is None
