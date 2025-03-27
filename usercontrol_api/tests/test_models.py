from django.test import TestCase
from ..models import *

class TestUser(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username='testuser', password='qwerty1234', email='testuser@example.com')

    def test_username(self):
        return self.assertEqual(self.user.username, 'testuser')