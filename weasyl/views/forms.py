import logging

import colander as c
from pyramid_deform import FormView as _FormView
from translationstring import TranslationStringFactory

from ..legacy import login_name
from ..models.users import Login


_ = TranslationStringFactory(__name__)
log = logging.getLogger(__name__)


class FormView(_FormView):
    def failure(self, exc):
        errors = [(t[-1].node, list(c.interpolate(t[-1].messages()))) for t in exc.error.paths()]
        log.debug('form failed to validate: %r', errors)
        return {'form': exc.field, 'errors': errors}

    def show(self, form):
        return {'form': form}


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
