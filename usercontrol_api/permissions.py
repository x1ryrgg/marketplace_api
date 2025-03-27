from django.shortcuts import get_object_or_404
from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _

from .models import User

class IsSuperUser(permissions.BasePermission):
    """
    Резрешение, которое позволяет использовать ресурс только пользователю с аттрибутом is_superuser.
    """
    message = "Вы не являетесь администратором приложения."

    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True
        return False

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        return False