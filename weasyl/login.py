from .dates import now


class LoginFailed(Exception):
    pass


class UserNeedsNewPassword(Exception):
    pass


def try_login(user, password, csrf_token=None):
    if user.bcrypt is None:
        raise LoginFailed('You need to create a new password; please use the password reset option.')
    if not user.bcrypt.does_authenticate(password):
        raise LoginFailed('Password incorrect.')
    user.last_login = now()
    return user.userid
