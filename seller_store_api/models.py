from django.db import models
from usercontrol_api.models import User


class Store(models.Model):
    author = models.ForeignKey(User, on_delete=models.SET_DEFAULT, default=1)
    name = models.CharField(max_length=100, unique=True, null=False, blank=False)
    description = models.CharField(max_length=1000, null=True, blank=True, default="Продавец не оставил описание об магазине.")
    email = models.CharField(max_length=124, null=True, blank=True)
    city = models.CharField(max_length=100, null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.email:
            self.email = self.author.email
        super().save(*args, **kwargs)

    def __str__(self):
        return "Author %s | Name %s | city %s" % (self.author, self.name, self.city)


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, null=False, blank=False)
    subcategory = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name="subcategories")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "Category %s | Subcategory %s" % (self.name, self.subcategory)

    def save(self, *args, **kwargs):
        # Проверяем, что категория не имеет более одного уровня вложенности
        if self.subcategory and self.subcategory.subcategory:
            raise ValueError("Категория не может иметь более одного уровня вложенности.")
        super().save(*args, **kwargs)

    @property
    def is_parent(self):
        """Проверяет, является ли категория родительской."""
        return not self.subcategory

    @property
    def is_child(self):
        """Проверяет, является ли категория дочерней."""
        return self.subcategory is not None


class Product(models.Model):
    name = models.CharField(max_length=128, unique=True, null=False, blank=False)
    price = models.DecimalField(max_digits=8, decimal_places=2, null=False, blank=False)
    quantity = models.PositiveIntegerField(null=False, blank=True, default=1)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=False, related_name="prdouct_categories")
    store = models.ForeignKey(Store, on_delete=models.SET_NULL, null=True, blank=False, related_name='product_store')
    description = models.CharField(max_length=1000, null=True, blank=True,
                                   default="Продавец не оставил описание об товаре.")
    update_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return 'Name %s | Price %s | Quantity %s | Store %s' % (self.name, self.price, self.quantity, self.store)







