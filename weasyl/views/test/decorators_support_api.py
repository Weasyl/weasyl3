from weasyl.views import decorators


@decorators.also_api_view(template='templates/basic.jinja2', name='basic')
def basic(context, request):
    return {'spam': 'eggs'}
