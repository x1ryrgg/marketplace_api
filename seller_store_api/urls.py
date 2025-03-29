from rest_framework import routers
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import *


store_router = DefaultRouter()
store_router.register(r'', StoreView, basename='store')

category_router = DefaultRouter()
category_router.register(r'', CategoriesView, basename='category'),

product_of_seller_router = DefaultRouter()
product_of_seller_router.register(r'', ProductOfSellerView, basename='products_of_seller')

products_router = DefaultRouter()
products_router.register(r'', ProductsView, basename='products')

# wishlist_router = DefaultRouter()
# wishlist_router.register(r'', WishListView, basename='wishlist')

urlpatterns = [
    path('seller/register/', SellerRegisterView.as_view({"get": "list",
                                                         "put": "update"}), name='seller-register'),
    path('store/', include(store_router.urls)),
    path('stores/', StoresAllView.as_view(), name='stores'),
    path('categories/', include(category_router.urls)),
    path('seller-products/', include(product_of_seller_router.urls)),
    path('products/', include(products_router.urls)),
    path('products/<int:id>/buy/', PayProductView.as_view(), name='buy_product'),
    path('products/<int:id>/add/', WishListAddView.as_view(), name='wishlist_add'),
    path('wishlist/', WishListView.as_view({"get": "list", "post": "payment_products"}), name='wishlist'),

]