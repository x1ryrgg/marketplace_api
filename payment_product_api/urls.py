from rest_framework import routers
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import *


wishlist_router = DefaultRouter()
wishlist_router.register(r'', WishListView, basename='wishlist')

urlpatterns = [
    path('wishlist/', include(wishlist_router.urls)),
    path('history/', HistoryView.as_view(), name='history'),
]