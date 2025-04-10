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
    path('products/<int:id>/buy/', PayProductView.as_view(), name='buy_product'),

    path('top-up/', CreateTopUpPaymentView.as_view(), name='create_top_up_payment'),
    path('yookassa-webhook/', yookassa_webhook, name='yookassa_webhook'),
]