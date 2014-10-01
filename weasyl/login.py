import arrow

from libweasyl.exceptions import LoginFailed


# XXX: move me to libweasyl

def try_login(user, password):
    """
    Try to log a user in, given their password.

    This will raise :py:exc:`~libweasyl.exceptions.LoginFailed` if the user
    doesn't have a bcrypted password stored or the password provided is
    incorrect.

    :param user: A :py:class:`~libweasyl.models.users.Login` object.
    :param password: A :py:class:`str` of the user's password.
    """
    if user.bcrypt is None:
        raise LoginFailed('You need to create a new password; please use the password reset option.')
    if not user.bcrypt.does_authenticate(password):
        raise LoginFailed('Password incorrect.')
    user.last_login = arrow.get()
    return user.userid
