from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from ..models import *
from usercontrol_api.models import WishlistItem, User
from rest_framework_simplejwt.tokens import AccessToken
from django.urls import reverse


class WishListAddView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='testuser', password='qwerty1234', email='testuser@example.com')

        cls.category = Category.objects.create(name='testcategory')

        cls.subcategory = SubCategory.objects.create(
            name='testsubcategory',
            category=cls.category)

        cls.product = Product.objects.create(
            name='testproduct',
            category=cls.subcategory,
            price=10,
            quantity=10)

        cls.product_variant = ProductVariant.objects.create(product=cls.product)

        cls.add_to_wishlist_url = reverse('wishlist_add', kwargs={'id': cls.product_variant.id})

    def setUp(self):
        self.client = APIClient()  # Используем APIClient из DRF
        self.token = self.generate_token_for_user(self.user)

    def generate_token_for_user(self, user):
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)

    def test_add_to_wishlist(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        # проверка до добавления
        wishlist_count = WishlistItem.objects.filter(user=self.user).count()
        self.assertEqual(wishlist_count, 0)

        # добавляем продукт в список желаемого в размере 3 шт
        request_data = {
            'quantity': 3
        }
        response = self.client.post(self.add_to_wishlist_url, data=request_data, format='json')
        self.assertEqual(response.status_code, 200)

        # проверерка ответа и quantity
        response_data = response.json()
        self.assertIn('добавлено', response_data)
        self.assertEqual(response_data['добавлено'], 'Было добавлено товаров: 3')

        # проверка количества товаров в wishlist
        new_count = WishlistItem.objects.filter(user=self.user).count()
        self.assertEqual(new_count, 1)

        # проверяем что именно тот продукт добавлен
        wishlist_item = WishlistItem.objects.get(user=self.user, product=self.product_variant)
        self.assertEqual(wishlist_item.product, self.product_variant)