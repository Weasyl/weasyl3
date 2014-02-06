DIRECTORS = {
    1014,  # Fiz
    2061,  # Inaki
    3,     # Kihari
    4393,  # Struguri
    5,     # Taw
}


TECHNICAL = {
    1019,  # Aden
    12834, # Catalepsy
    34165, # Charmander
    15224, # Foximile
    5173,  # Keet
    2303,  # Makyo
    2252,  # SuburbanFox
    5756,  # Weykent
}


ADMINS = DIRECTORS | TECHNICAL | {
    21,    # FayV
    2170,  # Matt
    2011,  # MLR
    1003,  # PunkJax
    1010,  # Stereo
    2542,  # Term
}


MODS = ADMINS | {
    1008,  # AdventureCat
    2076,  # Benji
    34256, # Lacuna
    22,    # Thestory
    2008,  # Tiger
}


groups = {}
for principal, userlist in [
        ('g:director', DIRECTORS),
        ('g:admin', ADMINS),
        ('g:mod', MODS),
        ('g:tech', TECHNICAL)]:
    for user in userlist:
        groups.setdefault(user, []).append(principal)
