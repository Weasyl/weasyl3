from .dates import now
from .legacy import login_name
from .models.users import Login


class LoginFailed(Exception):
    pass


class UserNeedsNewPassword(Exception):
    pass


def try_login(username, password):
    user = (
        Login.query
        .filter_by(login_name=login_name(username))
        .first())
    if user is None:
        raise LoginFailed()
    if user.bcrypt is None:
        raise UserNeedsNewPassword()
    if not user.bcrypt.does_authenticate(password):
        raise LoginFailed()
    user.last_login = now()
    return user.userid
