import random
from rest_framework import serializers
from .models import *


class RegisterSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'password')

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password']
        )
        Profile.objects.create(user=user)
        return user


class OpenUserSerializer(serializers.ModelSerializer):
    class YesNoField(serializers.BooleanField):
        def to_representation(self, instance):
            return "Yes" if instance else "No"

    is_seller = YesNoField()

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'is_seller')


class PrivateUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('id', 'username', 'balance', 'email', 'password', 'first_name', 'last_name', 'is_seller')


class ProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = Profile
        fields = ('id', 'user_id', 'image', 'date_of_birth')
        read_only_fields = ('user_id', )


class NotificationSerializer(serializers.ModelSerializer):
    class YesNoField(serializers.BooleanField):
        def to_representation(self, instance):
            return "Yes" if instance else "No"

    is_read = YesNoField()

    class Meta:
        model = Notification
        fields = ('id', 'title', 'is_read', 'created_at')


class RetrieveNotificationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Notification
        fields = ('id', 'title', 'message', 'created_at')


class CouponSerializer(serializers.ModelSerializer):

    class Meta:
        model = Coupon
        fields = ("id", 'user', 'code', 'discount', 'end_date')
        read_only_fields = ('user', )

    def create(self, validated_data):
        random_user = random.choice(User.objects.all())
        validated_data['user'] = random_user
        return Coupon.objects.create(**validated_data)

