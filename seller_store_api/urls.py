from rest_framework import routers
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import *


store_router = DefaultRouter()
store_router.register(r'', StoreView, basename='store')

all_stores_router = DefaultRouter()
all_stores_router.register(r'', StoresAllView, basename='stores'),

urlpatterns = [
    path('seller/register/', SellerRegisterView.as_view({"get": "list",
                                                         "put": "update"}), name='seller-register'),
    path('store/', include(store_router.urls)),
    path('stores/', include(all_stores_router.urls)),

    path('products/<int:id>/add/', WishListAddView.as_view(), name='wishlist_add'),

    # path('set/', SetCookie.as_view(), name=''),
    # path('get/', GetCookie.as_view(), name=''),
    # path('del/', DelCookie.as_view(), name='')
]