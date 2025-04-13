from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from product_control_api.models import Product
from usercontrol_api.models import User
from django.db.models import Q


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
        return "Store %s | Author %s" % (self.name, self.author)


class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_DEFAULT, default=1)
    product = models.ForeignKey('product_control_api.ProductVariant', on_delete=models.CASCADE, related_name='comments')
    photo = models.ImageField(upload_to='comments/', null=True, blank=True)
    stars = models.PositiveIntegerField(default=1, validators=[MinValueValidator(0), MaxValueValidator(5)])
    body = models.TextField(max_length=1000, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return 'User %s wrote a comment to product %s' % (self.user.username, self.product)

    class Meta:
        constraints = [
            models.CheckConstraint(
                name='star_raiting_valid',
                check=Q(stars__gte=1,stars__lte=5),
                violation_error_message='Можно ставить только от 1 до 5 звезд.'
            )
        ]







