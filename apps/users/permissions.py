from rest_framework import permissions

class IsAdminUserRole(permissions.BasePermission):
    """
    Allows access only to admin users.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'admin')

class IsAdminOrSelf(permissions.BasePermission):
    """
    Allows access to admin users or the user themselves.
    """
    def has_object_permission(self, request, view, obj):
        return bool(request.user and request.user.is_authenticated and (request.user.role == 'admin' or obj == request.user))
