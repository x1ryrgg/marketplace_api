from django.shortcuts import get_object_or_404
from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _

from usercontrol_api.models import User


class IsSeller(BasePermission):
    """
    Резрешение, которое позволяет использовать ресурс только пользователю с аттрибутом is_seller.
    """
    message = "Вы не являетесь продавцом. Этот район для продавцов ааааа"

    def has_permission(self, request, view):
        if request.user.is_seller:
            return True
        return False

    def has_object_permission(self, request, view, obj):
        if request.user.is_seller:
            return True
        return False