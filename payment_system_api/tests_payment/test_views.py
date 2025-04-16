from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from product_control_api.models import Category, SubCategory, ProductVariant, Product
from ..models import *
from usercontrol_api.models import WishlistItem, User
from django.urls import reverse


class PaymentViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='testuser', password='qwerty1234', email='testuser@example.com')
        cls.user.balance = 500
        cls.user.save()

        cls.category = Category.objects.create(name='testcategory')

        cls.subcategory = SubCategory.objects.create(
            name='testsubcategory',
            category=cls.category)

        cls.product = Product.objects.create(
            name='testproduct',
            category=cls.subcategory,
            price=10,
            quantity=10)

        cls.product_variant1 = ProductVariant.objects.create(product=cls.product, price=10, quantity=10)

        cls.product_variant2 = ProductVariant.objects.create(product=cls.product, price=50, quantity=20)

        cls.wishlist1 = WishlistItem.objects.create(user=cls.user, product=cls.product_variant1)
        cls.wishlist2 = WishlistItem.objects.create(user=cls.user, product=cls.product_variant2)

        cls.payment_response = reverse('buy_product', kwargs={'id': cls.product_variant1.id})

    def setUp(self):
        self.client = APIClient()  # Используем APIClient из DRF
        self.token = self.generate_token_for_user(self.user)

    def generate_token_for_user(self, user):
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)

    def test_pay_product_view(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        # проверка доставки пользователя до покупки
        delivery_count = Delivery.objects.filter(user=self.user).count()
        self.assertEqual(delivery_count, 0)

        # запрос
        response = self.client.post(self.payment_response)
        self.assertEqual(response.status_code, 200)

        # проверка доставки после покупки
        new_delivery_count = Delivery.objects.filter(user=self.user).count()
        self.assertEqual(new_delivery_count, 1)

        # проверка баланса после покупки
        self.user.refresh_from_db()
        self.assertEqual(self.user.balance, 490)

    def test_pay_product_wishlist_view(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        delivery_count = Delivery.objects.filter(user=self.user).count()
        self.assertEqual(delivery_count, 0)

        url = '/wishlist/buy/'
        data = {
            "products": [self.product_variant1.id, self.product_variant2.id]
        }
        response = self.client.post(url, data=data, format='json')
        self.assertEqual(response.status_code, 200)

        new_delivery_count = Delivery.objects.filter(user=self.user).count()
        self.assertEqual(new_delivery_count, 2)

        self.user.refresh_from_db()
        self.assertEqual(self.user.balance, 440)





