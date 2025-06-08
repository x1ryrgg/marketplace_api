from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsSeller(BasePermission):
    """
    Резрешение, которое позволяет использовать ресурс только пользователю с аттрибутом is_seller.
    """

    message = "Вы не являетесь продавцом."

    def has_permission(self, request, view):
        if request.user.is_seller:
            return True
        return False

    def has_object_permission(self, request, view, obj):
        if request.user.is_seller:
            return True
        return False
