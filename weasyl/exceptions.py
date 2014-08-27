class WeasylError(Exception):
    pass


class LoginFailed(WeasylError):
    pass


class ThumbnailingFuckedUp(WeasylError):
    pass
