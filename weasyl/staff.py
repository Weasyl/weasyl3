from libweasyl import staff

groups = {}


def init_groups():
    for principal, userlist in [
            ('g:director', staff.DIRECTORS),
            ('g:admin', staff.ADMINS),
            ('g:mod', staff.MODS),
            ('g:tech', staff.TECHNICAL)]:
        for user in userlist:
            groups.setdefault(user, []).append(principal)
