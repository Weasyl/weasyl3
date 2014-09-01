from pyramid.threadlocal import get_current_request

from .cache import region
from .models.media import SubmissionMediaLink, UserMediaLink
from .constants import DEFAULT_AVATAR


@SubmissionMediaLink.register_cache
@region.cache_multi_on_arguments()
def get_multi_submission_media(*submitids):
    request = get_current_request()
    return SubmissionMediaLink.bucket_links(request, submitids)


@UserMediaLink.register_cache
@region.cache_multi_on_arguments()
def get_multi_user_media(*userids):
    request = get_current_request()
    users_media = UserMediaLink.bucket_links(request, userids)

    for user_media in users_media:
        user_media.setdefault('avatar', DEFAULT_AVATAR)

    return users_media


def get_submission_media(submitid):
    return get_multi_submission_media(submitid)[0]


def get_user_media(userid):
    return get_multi_user_media(userid)[0]


def build_populator(identity, multi_get):
    def populator(objects):
        needy_objects = list({o for o in objects if not hasattr(o, 'media')})
        if not needy_objects:
            return objects
        keys_to_fetch = [getattr(o, identity) for o in needy_objects]
        for o, value in zip(needy_objects, multi_get(*keys_to_fetch)):
            o.media = value
        return objects
    return populator


populate_with_submission_media = build_populator('submitid', get_multi_submission_media)
populate_with_user_media = build_populator('userid', get_multi_user_media)
