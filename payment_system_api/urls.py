from rest_framework import routers
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import *


wishlist_router = DefaultRouter()
wishlist_router.register(r'', WishListView, basename='wishlist')

delivery_router = DefaultRouter()
delivery_router.register(r'', DeliveryView, basename='delivery')

urlpatterns = [
    path('wishlist/', include(wishlist_router.urls)),
    path('history/', HistoryView.as_view(), name='history'),
    path('delivery/', include(delivery_router.urls)),
]