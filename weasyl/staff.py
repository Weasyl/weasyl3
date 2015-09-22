from libweasyl.staff import DIRECTORS, TECHNICAL, ADMINS, MODS

groups = {}


def init_groups():
    for principal, userlist in [
            ('g:director', DIRECTORS),
            ('g:admin', ADMINS),
            ('g:mod', MODS),
            ('g:tech', TECHNICAL)]:
        for user in userlist:
            groups.setdefault(user, []).append(principal)
