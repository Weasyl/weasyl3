from pyramid.threadlocal import get_current_request

from .cache import region
from .models.media import SubmissionMediaLink, UserMediaLink


@SubmissionMediaLink.register_cache
@region.cache_multi_on_arguments()
def get_multi_submission_media(*submitids):
    request = get_current_request()
    return SubmissionMediaLink.bucket_links(request, submitids)


@UserMediaLink.register_cache
@region.cache_multi_on_arguments()
def get_multi_user_media(*userids):
    request = get_current_request()
    return UserMediaLink.bucket_links(request, userids)


def get_submission_media(submitid):
    return get_multi_submission_media(submitid)[0]


def get_user_media(userid):
    return get_multi_user_media(userid)[0]


def build_populator(identity, multi_get):
    def populator(objects):
        keys_to_fetch = [getattr(o, identity) for o in objects]
        for o, value in zip(objects, multi_get(*keys_to_fetch)):
            o.media = value
        return objects
    return populator


populate_with_submission_media = build_populator('submitid', get_multi_submission_media)
populate_with_user_media = build_populator('userid', get_multi_user_media)
