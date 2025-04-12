from django.contrib import admin
from .models import *

admin.site.register(Category)

admin.site.register(SubCategory)

admin.site.register(Product)

admin.site.register(VariantType)

admin.site.register(VariantOption)

admin.site.register(ProductVariant)
