from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import User


class RegisterViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("accounts:register")

    def test_register_success(self):
        resp = self.client.post(
            self.url,
            {
                "username": "newuser",
                "email": "new@test.com",
                "password": "StrongPass123!",
                "password2": "StrongPass123!",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertFalse("password" in resp.data)

    def test_register_password_mismatch(self):
        resp = self.client.post(
            self.url,
            {
                "username": "newuser",
                "email": "new@test.com",
                "password": "StrongPass123!",
                "password2": "DifferentPass!",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_duplicate_email(self):
        User.objects.create_user(username="existing", email="dup@test.com", password="StrongPass123!")
        resp = self.client.post(
            self.url,
            {
                "username": "newuser",
                "email": "dup@test.com",
                "password": "StrongPass123!",
                "password2": "StrongPass123!",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class LoginViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", email="test@test.com", password="StrongPass123!"
        )
        self.url = reverse("accounts:login")

    def test_login_success(self):
        resp = self.client.post(
            self.url, {"email": "test@test.com", "password": "StrongPass123!"}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("access", resp.data)
        self.assertIn("refresh", resp.data)

    def test_login_wrong_password(self):
        resp = self.client.post(
            self.url, {"email": "test@test.com", "password": "WrongPass!"}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class MeViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", email="test@test.com", password="StrongPass123!"
        )
        self.url = reverse("accounts:me")

    def test_me_authenticated(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["email"], "test@test.com")

    def test_me_unauthenticated(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)