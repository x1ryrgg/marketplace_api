from rest_framework import routers
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from .views import *


user_router = routers.DefaultRouter()
user_router.register(r'', UserView, basename='user')

notification_router = routers.DefaultRouter()
notification_router.register(r'', NotificationView, basename='notification')

coupon_router = routers.DefaultRouter()
coupon_router.register(r'', CouponView, basename='coupons')

urlpatterns = [
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('register/', RegisterView.as_view(), name='register'),

    path('users/', include(user_router.urls)),
    path('profile/', ProfileView.as_view({"get": "list", "patch": "partial_update"}), name='profile'),

    path('notifications/', include(notification_router.urls)),
    path('coupons/', include(coupon_router.urls)),

]