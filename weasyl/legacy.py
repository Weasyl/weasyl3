UNIXTIME_OFFSET = -18000


def plaintext(target):
    return ''.join(i for i in target if i.isalnum() and ord(i) < 128)


def login_name(target):
    return plaintext(target).lower()
