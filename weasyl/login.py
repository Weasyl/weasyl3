import arrow

from .exceptions import LoginFailed


def try_login(user, password, csrf_token=None):
    if user.bcrypt is None:
        raise LoginFailed('You need to create a new password; please use the password reset option.')
    if not user.bcrypt.does_authenticate(password):
        raise LoginFailed('Password incorrect.')
    user.last_login = arrow.get()
    return user.userid
