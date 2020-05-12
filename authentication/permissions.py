from rest_framework.permissions import BasePermission


class IsClientAdmin(BasePermission):
    """Grants client administrators full access"""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'CA'


class IsOwnerOrAdmin(BasePermission):
    """Grants client administrators full access"""

    def has_object_permission(self, request, view, obj):
        user = request.user
        return user.role == 'AA' or request.user == obj.client_admin


class IsProfileOwner(BasePermission):
    """allow only profile owners to update profiles"""

    def has_object_permission(self, request, view, obj):
        return request.user == obj.user