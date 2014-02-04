import datetime

import pytz


def now(tz=pytz.utc):
    return datetime.datetime.now(tz)
