from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum
from django.utils.translation import gettext_lazy as _


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class SubCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, unique=True, null=False, blank=False)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=128, null=False, blank=False)
    category = models.ForeignKey(SubCategory, on_delete=models.SET_NULL, null=True, blank=False, db_index=True, related_name="product_categories")
    price = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False)
    quantity = models.PositiveIntegerField(null=False, blank=True, default=1)
    store = models.ForeignKey('seller_store_api.Store', on_delete=models.SET_NULL, null=True, blank=False, related_name='product_store')
    description = models.CharField(max_length=1000, null=True, blank=True, default="Продавец не оставил описание о товаре.")
    update_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return 'Name %s | Store %s' % (self.name, self.store)

    @staticmethod
    def get_total_quantity_by_store(store_id):
        """ Возвращает общее количество товаров для указанного магазина """
        total = Product.objects.filter(store_id=store_id).aggregate(total_quantity=Sum('quantity'))['total_quantity']
        return total or 0


class VariantType(models.Model):
    name = models.CharField(max_length=100, null=False, blank=False)

    def __str__(self):
        return self.name


class VariantOption(models.Model):
    variant = models.ForeignKey(VariantType, on_delete=models.CASCADE)
    value = models.CharField(max_length=100, null=False, blank=False)

    def __str__(self):
        return "%s - %s" % (self.value, self.variant.name)


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    options = models.ManyToManyField(VariantOption, related_name='product_variants')
    price = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=True)
    quantity = models.PositiveIntegerField(null=False, blank=True)
    image = models.ImageField(upload_to='variant_images/', null=True, blank=True)
    views = models.PositiveIntegerField(default=0)
    description = models.CharField(max_length=500, blank=True, default="Продавец не оставил описание о товаре.")

    def __str__(self):
        str_options = ' | '.join(str(opt) for opt in self.options.all())
        return "%s - %s (Quantity: %s)" % (self.product.name, str_options, self.quantity)


