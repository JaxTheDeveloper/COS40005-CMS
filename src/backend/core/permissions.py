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


class IsConvenorOrStaffOrReadOnly(permissions.BasePermission):
    """Allow safe methods to any authenticated user; non-safe only to convenors or staff."""
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        user = request.user
        return bool(user and user.is_authenticated and (user.is_staff or getattr(user, 'user_type', None) == 'unit_convenor'))


class IsOwnerOrConvenorOrStaff(permissions.BasePermission):
    """Allow object edits to the owner, convenors, or staff; others read-only."""
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        user = request.user
        if not (user and user.is_authenticated):
            return False
        # owner check
        owner = getattr(obj, 'submitter', None) or getattr(obj, 'created_by', None) or getattr(obj, 'uploaded_by', None)
        if owner and owner == user:
            return True
        # convenor or staff
        if user.is_staff or getattr(user, 'user_type', None) == 'unit_convenor':
            return True
        return False
