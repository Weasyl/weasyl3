RATING_GENERAL = 10
RATING_MODERATE = 20
RATING_MATURE = 30
RATING_EXPLICIT = 40


RATING_NAME = {
    RATING_GENERAL: 'general',
    RATING_MODERATE: 'moderate',
    RATING_MATURE: 'mature',
    RATING_EXPLICIT: 'explicit',
}


SUBCATEGORIES = {
    1010: 'sketch',
    1020: 'traditional',
    1030: 'digital',
    1040: 'animation',
    1050: 'photography',
    1060: 'design / interface',
    1070: 'modeling / sculpture',
    1075: 'crafts / jewelry',
    1078: 'sewing / knitting',
    1080: 'desktop / wallpaper',
    1999: 'other visual',

    2010: 'story',
    2020: 'poetry / lyrics',
    2030: 'script / screenplay',
    2999: 'other literary',

    3010: 'original music',
    3020: 'cover version',
    3030: 'remix / mashup',
    3040: 'speech / reading',
    3500: 'embedded video',
    3999: 'other multimedia',
}


BLANK_AVATAR = '/static/images/avatar_default.jpg'


DEFAULT_AVATAR = [
    {
        'display_url': BLANK_AVATAR,
        'file_url': BLANK_AVATAR
    }
]
