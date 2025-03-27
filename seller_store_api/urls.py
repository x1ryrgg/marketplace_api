from rest_framework import routers
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import *


store_router = DefaultRouter()
store_router.register(r'', StoreView, basename='store')

urlpatterns = [
    path('seller/register/', SellerRegisterView.as_view({"get": "list",
                                                         "put": "update"}), name='seller-register'),
    path('store/', include(store_router.urls)),
    path('stores/', StoresAllView.as_view(), name='stores'),
]