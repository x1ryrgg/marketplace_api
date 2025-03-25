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
    permission_classes = [IsAuthenticated, IsSuperUser]
    serializer_class = UserSerializer
    queryset = User.objects.all()

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response(serializer.data)


class ProfileView(ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ProfileSerializer

    def get_queryset(self):
        queryset = Profile.objects.filter(user_id=self.request.user.id)
        return queryset

