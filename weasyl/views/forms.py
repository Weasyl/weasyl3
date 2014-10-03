import json
import logging

import colander as c
import deform.widget as w
from deform.exception import ValidationFailure
from deform.form import Form as _Form
from pyramid_deform import FormView as _FormView, CSRFSchema
from pyramid.view import view_config
from translationstring import TranslationStringFactory

from libweasyl.legacy import login_name
from libweasyl.models.users import Login
from .decorators import wraps_respecting_view_config


_ = TranslationStringFactory(__name__)
log = logging.getLogger(__name__)


def determine_errors(exc):
    """
    Pull out all of the error messages from a
    :py:class:`~deform.ValidationFailure`.

    This iterates over all of the error nodes in the underlying
    :py:class:`~colander.Invalid`, using :py:meth:`~colander.Invalid.paths`.
    Importantly, this calls (the apparently undocumented)
    :py:func:`colander.interpolate` on each error message, producing error
    messages without ``${}`` in them.

    :param exc: A :py:class:`deform.ValidationFailure`.
    :returns: A list of ``node, errors`` tuples, where each ``node`` is the
        :py:class:`~colander.SchemaNode` which failed to validate and
        ``errors`` is a list of :py:class:`str` error messages.
    """
    return [(t[-1].node, list(c.interpolate(t[-1].messages()))) for t in exc.error.paths()]


class Form(_Form):
    """
    Basic extensions of deform's :py:class:`~deform.Form`.
    """

    focus_on_submit = False
    """
    Whether the form's submit button should have an ``autofocus`` attribute set
    on it.
    """

    def determine_autofocus(self):
        """
        Determine which form field should be autofocused.

        This will autofocus on the first non-hidden form element with an error.
        If no form elements match these criteria, the form's submit button will
        get focus. This is done by setting the :py:attr:`.focus_on_submit`
        attribute to :py:data:`True`.
        """
        for field in self:
            if not field.error or isinstance(field.widget, w.HiddenWidget):
                continue
            field.autofocus = True
            log.debug('%r autofocused %r', self, field)
            return
        log.debug("%r couldn't autofocus anything", self)
        self.focus_on_submit = True


class FormView(_FormView):
    """
    Basic extensions of pyramid_deform's :py:class:`~pyramid_deform.FormView`.

    This class is intended to be subclassed to provide behavior. Specifically,
    subclasses should override :py:attr:`~pyramid_deform.FormView.buttons` and
    :py:attr:`~pyramid_deform.FormView.schema` to indicate how to validate the
    form.

    As pyramid_deform is not very extremely detailed, here is how
    :py:class:`.FormView` works and how to subclass it:

    Most important is the :py:attr:`~pyramid_deform.FormView.schema` attribute,
    which controls which :py:class:`colander.Schema` is used to validate the
    form data. This must be overridden in subclasses.

    :py:attr:`~pyramid_deform.FormView.buttons` must also be overridden in
    subclasses, as it indicates which form element names are used by the submit
    buttons on the form. See the *buttons* argument to :py:class:`deform.Form`
    for its format.

    For each button, there must be a corresponding success method on the
    subclass. Success methods are named after the button name. So, for a
    :py:class:`.FormView` with a :py:attr:`~pyramid_deform.FormView.buttons` of
    ``('spam', 'eggs')``, there must be corresponding ``spam_success`` and
    ``eggs_success`` methods on the subclass. These methods are called after
    validation succeeds, with a single argument: the parsed form data. The
    method should return :py:data:`None` or a :py:class:`dict` to show the form
    again or some response, which will be returned as-is. If a :py:class:`dict`
    is returned, it will be passed to the renderer directly. If :py:data:`None`
    is returned, :py:meth:`.show` will be called to get the :py:class:`dict` to
    pass to the renderer.

    Optionally, a failure method can be defined for a button to indicate what
    should happen if validation fails after clicking that button. These methods
    are named e.g. ``spam_failure`` or ``eggs_failure`` and are called with a
    single argument: an instance of :py:class:`deform.ValidationFailure`. The
    return value of a failure method is treated exactly like that of a success
    method.
    """

    form_class = Form
    """
    Defaults to :py:class:`.Form`.

    It's rare to need to replace this.
    """

    form_key = '_form'
    """
    The key to use in the :py:class:`dict` passed to the renderer for the
    :py:attr:`.form_class` instance. This is used by the default
    :py:meth:`.show` and :py:meth:`.failure`.
    """

    errors_key = '_errors'
    """
    The key to use in the :py:class:`dict` passed to the renderer for the
    :py:class:`deform.ValidationFailure` instance. This is used by the default
    :py:meth:`.failure`.
    """

    def extra_fields(self):
        """
        Extra fields to pass to the renderer.

        By default, returns an empty :py:class:`dict`. This is called by the
        default :py:meth:`.show` and :py:meth:`.failure`.

        :returns: A :py:class:`dict`.
        """
        return {}

    def failure(self, exc):
        """
        The default method to call if form validation fails and there is no
        failure method for the button pressed.

        By default, returns *exc* under the :py:attr:`.errors_key` and
        *exc.field* under the :py:attr:`.form_key`.

        :param exc: A :py:class:`deform.ValidationFailure`.
        :returns: A :py:class:`dict`.
        """
        errors = determine_errors(exc)
        log.debug('form failed to validate: %r', errors)
        ret = {self.form_key: exc.field, self.errors_key: errors}
        ret.update(self.extra_fields())
        exc.field.determine_autofocus()
        return ret

    def show(self, form):
        """
        The default method to call if the success or failure method for the
        button pressed returns :py:data:`None`.

        By default, returns *form* under the :py:attr:`.form_key`.

        :param form: An instance of :py:attr:`.form_class`.
        :returns: A :py:class:`dict`.
        """
        ret = {self.form_key: form}
        ret.update(self.extra_fields())
        return ret


class User(c.SchemaType):
    def serialize(self, node, appstruct):
        if appstruct is c.null:
            return appstruct
        return appstruct.profile.username

    def deserialize(self, node, cstruct):
        if cstruct is c.null:
            return cstruct
        user = Login.query.filter_by(login_name=login_name(cstruct)).first()
        if user is None:
            raise c.Invalid(node, _('"${val}" is not a valid username', mapping=dict(val=cstruct)))
        return user


class JSON(c.SchemaType):
    def serialize(self, node, appstruct):
        if appstruct is c.null:
            return appstruct
        return json.dumps(appstruct)

    def deserialize(self, node, cstruct):
        if cstruct is c.null:
            return cstruct
        try:
            return json.loads(cstruct)
        except ValueError as e:
            raise c.Invalid(node, _('"${val}" is not valid JSON', mapping=dict(val=cstruct))) from e


def form_renderer(schema, key, *, success, button, **kwargs):
    """
    A decorator for handling incidental forms on a page.

    :py:func:`.form_renderer` is unlike :py:class:`.FormView` in that
    :py:class:`.FormView` is intended for a page containing a single form,
    where the entire point of the page is displaying that form. An "incidental
    form" is, for example, the "add a comment" form on a submission page--not
    the primary focus of the page, but it still needs to be validated and
    refilled like a :py:class:`.FormView` form. Additionally, a view function
    can have multiple :py:func:`.form_renderer` decorations attached to it for
    rendering multiple incidental forms on the page.

    This works by defining a wrapper function which creates and validates the
    appropriate form object. Pyramid :term:`view configuration` is done on the
    wrapper using *kwargs* to set up the predicates for the form's target URL.
    For example::

      @form_renderer(Schema, 'form', success=success, button='submit',
                     name='form')

    *kwargs* will be ``{'name': 'form'}`` in this case, and as such, the
    :term:`view configuration` done for the wrapper function will be equivalent
    to::

      @view_config(name='form', request_method='POST')

    The ``request_method='POST'`` is automatically added by
    :py:func:`.form_renderer`. A more realistic, complete example would be like
    this::

      @view_config(renderer='index.jinja2')
      @form_renderer(SchemaA, 'form_a', success=success_a, button='submit',
                     name='form-a', renderer='index.jinja2')
      @form_renderer(SchemaB, 'form_b', success=success_b, button='submit',
                     name='form-b', renderer='index.jinja2')
      def index(context, request, forms):
          ret = forms.copy()
          ret['notice'] = request.db.Notices.query.first()
          return ret

    In this example, three URLs are defined. Following the order of the
    decorators, this allows a client to :http:method:`GET` ``/``,
    :http:method:`POST` to ``/form-a``, and :http:method:`POST` to
    ``/form-b``. If this doesn't make sense yet, consider reviewing the pyramid
    documentation on :term:`traversal` and :term:`view configuration`.

    Anyway, the :term:`view callable` ``index`` will be called in the following
    circumstances:

    - A :http:method:`GET` to ``/``, because of the first ``@view_config``.

    - A :http:method:`POST` to ``/form-a`` or ``/form-b``, because of the
      implicit ``@view_config`` done when doing ``@form_renderer``. However,
      in this case, ``index`` will only be called if either of the following
      things happened:

      - The form data did not validate against the appropriate schema
        (i.e. ``SchemaA`` for a :http:method:`POST` to ``/form-a``). In this
        case, the errors for the form will also be included in the ``forms``
        parameter to ``index``.

      - Validating the form data wasn't attempted, because the button name
        passed to :py:func:`.form_renderer` (``submit``) wasn't present in the
        form data.

    In fact, ``index`` is only *not* called if the form data validated against
    appropriate schema. In that case, ``success_a`` or ``success_b`` will be
    called, depending on which endpoint received the :http:method:`POST`. The
    signatures of these functions is similar to that of ``index``::

      def success_a(context, request, appstruct):
          return render_to_response('json', appstruct, request=request)

    The *context* and *request* parameters are passed the same data that a
    :term:`view callable` would be passed. *appstruct* is the validated,
    decoded form data. This function must itself return a complete
    :term:`response`.
    """
    form_key = '_%s_form' % (key,)
    errors_key = '_%s_errors' % (key,)

    def select_form(func):
        def wrapper(context, request):
            request._selected_form = key
            return func(context, request)
        return wrapper

    def deco(func):
        @view_config(_depth=1, request_method='POST', decorator=select_form, **kwargs)
        @wraps_respecting_view_config(func)
        def wrapper(context, request, forms=()):
            forms = dict(forms)
            form = forms[form_key] = Form(schema().bind(request=request))
            forms[errors_key] = None
            selected_form = getattr(request, '_selected_form', None)

            if selected_form == key and button in request.POST:
                controls = request.POST.items()
                try:
                    validated = form.validate(controls)
                except ValidationFailure as exc:
                    forms[errors_key] = determine_errors(exc)
                    form.determine_autofocus()
                else:
                    return success(context, request, validated)

            return func(context, request, forms=forms)
        return wrapper
    return deco


class CommentForm(CSRFSchema):
    comment = c.SchemaNode(
        c.String(), description="Comment", widget=w.TextAreaWidget(
            css_class='comment-entry', placeholder="Share your thoughts\u2026"))
