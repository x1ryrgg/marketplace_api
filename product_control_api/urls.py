from .views import *
from django.urls import path, include
from rest_framework.routers import DefaultRouter


category_router = DefaultRouter()
category_router.register(r'', CategoriesView, basename='category'),

product_of_seller_router = DefaultRouter()
product_of_seller_router.register(r'', ProductOfSellerView, basename='products_of_seller')

products_router = DefaultRouter()
products_router.register(r'', ProductsView, basename='products')

urlpatterns = [
    path('categories/', include(category_router.urls)),

    path('seller-products/', include(product_of_seller_router.urls)),
    path('products/', include(products_router.urls)),
]