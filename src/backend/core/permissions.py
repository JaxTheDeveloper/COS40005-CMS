from rest_framework import permissions


class IsStaff(permissions.BasePermission):
    """Allow access only to staff users."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class IsConvenor(permissions.BasePermission):
    """Allow access only to unit convenors (user_type 'unit_convenor')."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and getattr(request.user, 'user_type', None) == 'unit_convenor')


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Object-level permission to allow owners to edit objects, others read-only."""
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        # Assume objects have 'submitter' or 'created_by' or 'uploaded_by'
        owner = getattr(obj, 'submitter', None) or getattr(obj, 'created_by', None) or getattr(obj, 'uploaded_by', None)
        return bool(owner and owner == request.user)
