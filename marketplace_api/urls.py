"""
URL configuration for marketplace_api project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions


schema_view = get_schema_view(
    openapi.Info(
        title="Marketplace API",  # Название вашего API
        default_version='v1',    # Версия API
        description="Реализация API маркетплейса",  # Описание API
        contact=openapi.Contact(email="barya_barya@example.com"),  # Контактная информация
        license=openapi.License(name="BSD License"),  # Лицензия (опционально)
    ),
    public=True,  # Доступно ли API публично
    permission_classes=(permissions.AllowAny,),  # Разрешения для просмотра документации
)

# Глобальные настройки Swagger
swagger_settings = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
        },
    },
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('usercontrol_api.urls')),
    path('', include('seller_store_api.urls')),
    path('', include('payment_system_api.urls')),
    path('', include('product_control_api.urls')),

    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    # ReDoc UI
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
