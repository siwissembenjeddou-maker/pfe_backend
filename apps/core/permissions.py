from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """Allow only admin users."""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'admin'


class IsPsychologist(BasePermission):
    """Allow admin and psychologist users."""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role in ('admin', 'psychologist')


class IsParent(BasePermission):
    """Allow admin and parent users."""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role in ('admin', 'parent')


class IsEducator(BasePermission):
    """Allow admin and educator users."""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role in ('admin', 'educator')


class IsParentOrReadOnly(BasePermission):
    """Allow parents to only read their own children's data."""
    def has_permission(self, request, view):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return request.user and request.user.is_authenticated
        return request.user and request.user.is_authenticated and request.user.role in ('admin', 'parent')


class IsPsychologistOrReadOnly(BasePermission):
    """Allow psychologists to read and write; others can only read."""
    def has_permission(self, request, view):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return request.user and request.user.is_authenticated
        return request.user and request.user.is_authenticated and request.user.role in ('admin', 'psychologist')
