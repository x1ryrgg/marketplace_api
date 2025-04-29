from typing import Any

from django.core.exceptions import ObjectDoesNotExist
from django.db.models.sql import Query
from django.shortcuts import render
from rest_framework_extensions.cache.mixins import CacheResponseMixin
from django.core.cache import cache
from rest_framework import generics, status, permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from rest_framework.exceptions import ValidationError, PermissionDenied
from django.utils.translation import gettext_lazy as _
from .models import *
from .permissions import *
from .serializers import *
from rest_framework.response import Response


class RegisterView(generics.CreateAPIView):
    """ Endpoint для регистрации пользователей
    url: /register/
    body: username (str), password (str), email (str)
    """
    queryset = User.objects.all()
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserView(ModelViewSet):
    """ Endpoint для просмотра всех пользователей (доступно только superuser-ам)
    url: /users/
    """
    permission_classes = [IsAuthenticated, IsSuperUser]
    serializer_class = OpenUserSerializer
    queryset = User.objects.all()
    http_method_names = ['get']

    def retrieve(self, request, *args, **kwargs) -> Response:
        user = self.get_object()
        profile = Profile.objects.get(user=user)
        data = {
            'user': self.get_serializer(user).data,
            "user_profile": ProfileSerializer(profile).data
        }
        return Response(data)


class ProfileView(ModelViewSet, CacheResponseMixin):
    """ Endpoint для просмотра профиля, а также купонов.
    url: /profile/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ProfileSerializer
    http_method_names = ['get', 'patch']
    list_cache_timeout = 120

    def get_queryset(self):
        return Profile.objects.filter(user=self.request.user.id)

    def get_object(self):
        try:
            return Profile.objects.get(user=self.request.user.id)
        except Exception:
            return None

    def list(self, request, *args, **kwargs) -> Response:
        profile = self.get_object()
        user = request.user
        coupons = Coupon.objects.filter(user=user)
        data = {
            'непрочитанные уведомления': Notification.objects.filter(user=self.request.user, is_read=False).count(),
            'профиль': self.get_serializer(profile).data,
            'ваш аккаунт': PrivateUserSerializer(user, many=False).data,
            'ваши купоны': CouponSerializer(coupons, many=True).data
        }
        return Response(data)

    def partial_update(self, request, *args, **kwargs):
        """ Изменение профиля """
        profile = self.get_queryset().get()

        serializer = self.get_serializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        self.perform_update(serializer)
        return Response(serializer.data)


class NotificationView(CacheResponseMixin, ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer
    http_method_names = ['get', 'delete', 'post']
    list_cache_timeout = 100

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).select_related('user').order_by("is_read", '-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        unread_count = Notification.objects.filter(user=self.request.user, is_read=False).count()
        serializer = self.get_serializer(queryset, many=True)

        return Response({
            "Непрочитанные уведомления": unread_count,
            'Уведомления': serializer.data,
        })


    def retrieve(self, request, *args, **kwargs) -> Response:
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=['is_read'])
        serializer = RetrieveNotificationSerializer(notification)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        notification = self.get_object()
        self.perform_destroy(notification)
        return Response(_(f"Уведомление удалено."))


class AdminNotificationView(APIView):
    """ Endpoint для создания уведомлений-рассылок (только superuser-ам)
    url: /notification/admin/
    body: title (str, Optional), message (str, Optional)
    """
    permission_classes = [IsAuthenticated, IsSuperUser]
    serializer_class = NotificationSerializer

    def post(self, request, *args, **kwargs) -> Response:
        users = [user for user in User.objects.filter(is_superuser=False)]
        title = request.data.get('title', Notification.TitleChoice.OTHER)
        message = request.data.get('message', None)

        notifications = []
        for user in users:
            notification = Notification.objects.create(
                user=user,
                title=title,
                message=message
            )
            notifications.append(notification)

        serializer = self.serializer_class(notifications[-1])
        return Response({
            'count_of_receivers': len(users),
            'type_of_message': serializer.data
        })

class CouponView(ModelViewSet):
    """ Endpoint для просмотра всех купонов, а также для тестового создания купонов (доступно superuser-ам)
    url: /coupons/
    """
    permission_classes = [IsAuthenticated, IsSuperUser]
    serializer_class = CouponSerializer
    queryset = Coupon.objects.all()
    http_method_names = ['get', 'post']

    def perform_create(self, serializer) -> Response:
        serializer.save()
        return Response(serializer.data)


def _create_coupon_with_chance(user: User) -> Coupon | None:
    """ Создает купон с вероятностью 30% """
    if random.random() < 0.3:  # 30% шанс
        coupon = Coupon.objects.create(user=user)
        return coupon
    return None