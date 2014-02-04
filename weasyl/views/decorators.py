from decorator import decorator
from pyramid.renderers import render_to_response


@decorator
def requires_no_login(f, request):
    if request.session['userid']:
        return render_to_response(
            'errors/generic.jinja2', {'message': 'You must be signed out.'})
    return f(request)
