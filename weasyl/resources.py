import logging

from pyramid.security import Authenticated, Allow, Everyone, Deny
from pyramid import httpexceptions

from libweasyl.models.content import Submission
from libweasyl.models.users import Login

log = logging.getLogger(__name__)


class Resource(object):
    """Base class for a URL traversal resource.

    Resources extending this class should provide a `children` dict, which maps
    strings to types. During traversal, an instance's __getitem__ is called with
    the next resource name. The resource type to return is looked up using this
    dict, which will automatically raise the required KeyError if a child is not
    found.

    By default, every resource has an __acl__ attribute that Allows a "view"
    permission to Everyone. Override this attribute to restrict resources.

    TODO: permission names should be kept in a module of constants.

    Attributes:
        request: The request being served
        children (dict): A dict mapping names of child resources to their type
    """

    __acl__ = (
        (Allow, Everyone, "view"),
    )

    def __init__(self, request):
        """Initialize a Resource

        Args:
            request: The request being served
        """
        self.request = request

    def __getitem__(self, item):
        """Return a location-aware child resource instance.

        Args:
            item (str): The name of the child

        Returns:
            The location-aware child resource

        Raises:
            KeyError: If no child is found
        """
        child_obj = self.children[item](self.request)
        child_obj.__name__ = item
        child_obj.__parent__ = self
        return child_obj


class DispatcherResource(Resource):
    """A resource whose children are found in a database, for example.

    When a child resource is requested, an instance's __getitem__ method will
    first check the `children` dict (as per Resource) for a child type of the
    given name. If one is not found, a class of `child_resource_type` will be
    instantiated and returned.

    The `child_resource_type` attribute should be overridden to indicate the
    appropriate child type to return. E.g., for a UserDispatcher resource, this
    might be set to UserResource.

    The child resource should always expect it's name as a string, even if it is
    identified by an integer in a database, for example.

    Instantiating the child object must never have any side effects.

    Children resources must have an `exists` attribute, which is either True or
    False depending on whether or not the resource is actually found in the
    underlying storage. For "GET" and "POST" requests, `exists` must be True or
    else a KeyError will be raised (resulting in a 404). "PUT" and "DELETE" do
    not require this.

    TODO: resources where "PATCH" is relevant might also require `exists` to be
    True.

    Attributes:
        child_resource_type (type): The child resource class
    """

    def __getitem__(self, item):
        try:
            # Try to find a "regular" child resource first
            return super().__getitem__(item)
        except KeyError:
            # Otherwise, make a child_resource_type
            child_obj = self.child_resource_type(self.request)
            child_obj.__name__ = item
            child_obj.__parent__ = self

            # If relevant, make sure it represents an existing resource
            if self.request.method in ("GET", "POST") \
                    and child_obj.exists is not True:
                raise KeyError(item)

            return child_obj


class SubmissionResource(Resource):
    """Resource representing a submission.

    Note that there is no code for _checking_ permissions in this resource.
    Instead, the ACL is set up, and each view will specify the permission
    required.

    Attributes:
        id (int): The submission's integer identifier
    """

    def __acl__(self):
        """Return the ACL.

        This is an instance method, because each submission may have different
        restrictions on it (e.g. "friends only" or content ratings). For a
        mature submission, you might have an (Allow, CAN_VIEW_MATURE, "view")
        entry or something.

        Deny should be the default last item.
        """
        # TODO
        return (
            (Deny, Everyone, "view"),
        )

    def __init__(self, request):
        super().__init__(request)

        self.children = {
            # "comments": ...,
        }

    @property
    def id(self):
        return int(self.__name__)

    @property
    def exists(self):
        try:
            # FIXME: replace this with an exists query (or better yet, test a
            # reified attribute of this object that will load the submission
            # from the DB).
            submission = Submission.query.get_or_404(self.id)

            if not submission:
                return False
            else:
                return True

        except ValueError:
            return False


class SubmissionDispatcher(DispatcherResource):
    child_resource_type = SubmissionResource


class RootResource(Resource):
    def __init__(self, request):
        super().__init__(request)

        self.children = {
            "submissions": SubmissionDispatcher,
        }

        # Special case of location-aware info, for the root resource only
        self.__name__ = ""
        self.__parent__ = None

# class IntermediateResource:
#     @classmethod
#     def insert(cls, child, segment):
#         inst = cls()
#         inst.__name__ = child.__name__
#         inst.__parent__ = child.__parent__
#         child.__name__ = segment
#         child.__parent__ = inst
#         return child
#
#
# def make_location_aware(func):
#     def __getitem__(self, segment):
#         ret = func(self, segment)
#         ret.__name__ = segment
#         ret.__parent__ = self
#         return ret
#
#     return __getitem__
#
#
# def userid_from_principals(principals):
#     return next((p for p in principals if isinstance(p, int)), None)
#
#
# class SubmissionsResource:
#     def __init__(self, request):
#         self.request = request
#
#     @make_location_aware
#     def __getitem__(self, segment):
#         if not segment.isdigit():
#             raise KeyError(segment)
#         submission = Submission.query.get_or_404(segment)
#         if isinstance(self.__parent__,
#                       UserResource) and self.__parent__.user != submission.owner:
#             raise httpexceptions.HTTPNotFound()
#         return SubmissionResource(self.request, submission)
#
#
# class SubmissionResource:
#     def __init__(self, request, submission):
#         self.request = request
#         self.submission = submission
#
#     def __getitem__(self, segment):
#         if segment == 'mod':
#             return IntermediateResource.insert(self, segment)
#         raise KeyError(segment)
#
#     def permits_view(self, principals):
#         # XXX: this probably needs more checks
#         if 'g:mod' in principals and (
#                         self.request.traversed[-1] == 'mod'
#                 or self.request.GET.get('anyway') == 'true'):
#             return True
#         if 'hidden' in self.submission.settings:
#             return False
#         if 'friends-only' in self.submission.settings:
#             userid = userid_from_principals(principals)
#             return userid and self.submission.owner.is_friends_with(userid)
#         return True
#
#     def permits_comment(self, principals):
#         # XXX: this needs more checks
#         if not self.permits_view(principals):
#             return False
#         return Authenticated in principals
#
#
# class UsersResource:
#     def __init__(self, request):
#         self.request = request
#
#     @make_location_aware
#     def __getitem__(self, segment):
#         user = Login.query.filter_by(login_name=segment).first_or_404()
#         return UserResource(self.request, user)
#
#
# class MethodDispatchResource:
#     def __init__(self, request):
#         self.request = request
#
#     @make_location_aware
#     def __getitem__(self, segment):
#         factory = getattr(self, 'segment_' + segment, None)
#         if factory is None:
#             raise KeyError(segment)
#         return factory(self.request)
#
#
# class UserResource(MethodDispatchResource):
#     def __init__(self, request, user):
#         self.request = request
#         self.user = user
#
#     def permits_view(self, principals):
#         # XXX: this probably needs more checks
#         if 'hide-profile-from-guests' in self.user.profile.settings:
#             return Authenticated in principals
#         return True
#
#     def permits_shout(self, principals):
#         # XXX: this needs more checks
#         if not self.permits_view(principals):
#             return False
#         return Authenticated in principals
#
#     segment_submissions = SubmissionsResource
#
#
# class OAuth2Resource(MethodDispatchResource):
#     pass
#
#
# class APIv2Resource(MethodDispatchResource):
#     segment_oauth2 = OAuth2Resource
#     segment_submissions = SubmissionsResource
#     segment_users = UsersResource
#
#     def __getitem__(self, segment):
#         if segment == '_debug' and self.request.is_debug_on:
#             return DebugResource(self.request)
#         return super().__getitem__(segment)
#
#
# class APIResource(MethodDispatchResource):
#     segment_v2 = APIv2Resource
#
#
# class DebugResource(MethodDispatchResource):
#     pass
#
#
# class RootResource(MethodDispatchResource):
#     __name__ = ''
#     __parent__ = None
#
#     segment_submissions = SubmissionsResource
#     segment_users = UsersResource
#     segment_api = APIResource
#
#     def __getitem__(self, segment):
#         if segment.startswith('~'):
#             return UsersResource(self.request)[segment[1:]]
#         elif segment == '_debug' and self.request.is_debug_on:
#             return DebugResource(self.request)
#         return super().__getitem__(segment)
#
#     def permits_signin(self, principals):
#         return Authenticated not in principals
#
#     def permits_signout(self, principals):
#         return Authenticated in principals
