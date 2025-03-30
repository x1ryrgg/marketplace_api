from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render
from rest_framework import generics, status, permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from rest_framework.exceptions import ValidationError, PermissionDenied
from django.utils.translation import gettext_lazy as _
from .models import *
from .permissions import *
from .serializers import *
from rest_framework.response import Response


class RegisterView(generics.CreateAPIView):
    """ Endpoint для регистрации пользователей"""
    queryset = User.objects.all()
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        """
        Регистрация пользователя
        url: /register/
        body: username (str), password (str), email (str)
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserView(ModelViewSet):
    """ Endpoint для просмотра всех пользователей (доступно только админу)
    url: /users/
    """
    permission_classes = [IsAuthenticated, IsSuperUser]
    serializer_class = OpenUserSerializer
    queryset = User.objects.all()
    http_method_names = ['get']

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        user = self.get_object()
        profile = Profile.objects.get(user=user)
        data = {
            'user': self.get_serializer(user).data,
            "user_profile": ProfileSerializer(profile).data
        }
        return Response(data)


class ProfileView(ModelViewSet):
    """ Endpoint для просмотра своего профиля и его изменения.
    url: /profile/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ProfileSerializer
    http_method_names = ['get', 'patch']

    def get_queryset(self):
        return Profile.objects.filter(user=self.request.user.id)

    def get_object(self):
        try:
            return Profile.objects.get(user=self.request.user.id)
        except Exception:
            return None

    def list(self, request, *args, **kwargs):
        profile = self.get_object()
        user = request.user
        data = {
            'profile': self.get_serializer(profile).data,
            'user': PrivateUserSerializer(user, many=False).data
        }
        return Response(data)

    def partial_update(self, request, *args, **kwargs):
        profile = self.get_queryset().get()

        serializer = self.get_serializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        self.perform_update(serializer)
        return Response(serializer.data)