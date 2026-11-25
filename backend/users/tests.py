import re
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from rest_framework.test import APIClient


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class CustomerEmailOTPTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_email_otp_registers_and_authenticates_customer_without_phone(self):
        response = self.client.post("/api/auth/otp/request/", {"email": "Fresh.Customer@example.com"}, format="json")
        self.assertEqual(response.status_code, 202)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("fresh.customer@example.com", mail.outbox[0].to)
        code = re.search(r"\b(\d{6})\b", mail.outbox[0].body).group(1)

        response = self.client.post("/api/auth/otp/verify/", {"email": "FRESH.CUSTOMER@example.com", "code": code}, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        user = get_user_model().objects.get(email="fresh.customer@example.com")
        self.assertIsNone(user.phone_number)
        self.assertIsNotNone(user.email_verified_at)
        self.assertFalse(user.has_usable_password())

    @patch("users.services.generate_otp", side_effect=["123456", "654321"])
    def test_resending_otp_invalidates_the_previous_code_and_sends_branded_html(self, _generate_otp):
        self.client.post("/api/auth/otp/request/", {"email": "resend@example.com"}, format="json")
        old_code = re.search(r"\b(\d{6})\b", mail.outbox[-1].body).group(1)
        self.assertEqual(len(mail.outbox[-1].alternatives), 1)
        self.assertIn("Your sign-in code", mail.outbox[-1].alternatives[0][0])
        self.assertIn("resend@example.com", mail.outbox[-1].to)

        self.client.post("/api/auth/otp/request/", {"email": "resend@example.com"}, format="json")
        new_code = re.search(r"\b(\d{6})\b", mail.outbox[-1].body).group(1)
        self.assertNotEqual(old_code, new_code)

        old_response = self.client.post("/api/auth/otp/verify/", {"email": "resend@example.com", "code": old_code}, format="json")
        new_response = self.client.post("/api/auth/otp/verify/", {"email": "resend@example.com", "code": new_code}, format="json")
        self.assertEqual(old_response.status_code, 400)
        self.assertEqual(new_response.status_code, 200)

    def test_user_can_add_optional_profile_phone_after_login(self):
        user = get_user_model().objects.create_user(username="email-customer", email="customer@example.com")
        self.client.force_authenticate(user)

        response = self.client.patch("/api/auth/me/", {"phone_number": "+919876543210"}, format="json")

        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertEqual(user.phone_number, "+919876543210")

    def test_customer_otp_cannot_authenticate_staff_account(self):
        user = get_user_model().objects.create_user(username="staff-account", email="staff@example.com", is_staff=True)
        self.client.post("/api/auth/otp/request/", {"email": user.email}, format="json")
        code = re.search(r"\b(\d{6})\b", mail.outbox[-1].body).group(1)

        response = self.client.post("/api/auth/otp/verify/", {"email": user.email, "code": code}, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertNotIn("access", response.data)

    def test_superuser_creation_does_not_require_customer_phone(self):
        user = get_user_model().objects.create_superuser(username="staff-admin")

        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertIsNone(user.phone_number)


class APIEndpointPermissionTests(TestCase):
    """Keep customer and staff API routes private unless explicitly public."""

    def setUp(self):
        self.client = APIClient()

    def test_customer_account_cart_and_order_endpoints_require_authentication(self):
        protected_requests = [
            ("get", "/api/auth/me/", None),
            ("get", "/api/auth/addresses/", None),
            ("post", "/api/auth/addresses/", {}),
            ("get", "/api/cart/", None),
            ("post", "/api/cart/items/", {}),
            ("get", "/api/orders/", None),
            ("post", "/api/orders/", {}),
            ("get", "/api/orders/delivery-area/", None),
            ("post", "/api/orders/delivery-quote/", {}),
        ]

        for method, url, payload in protected_requests:
            with self.subTest(method=method, url=url):
                response = getattr(self.client, method)(url, payload, format="json") if payload is not None else getattr(self.client, method)(url)
                self.assertEqual(response.status_code, 401)

    def test_staff_management_endpoints_require_staff_session(self):
        protected_requests = [
            ("get", "/api/staff/me/", None),
            ("get", "/api/staff/dashboard/", None),
            ("get", "/api/staff/users/", None),
            ("post", "/api/staff/categories/", {}),
            ("patch", "/api/staff/delivery-area/", {}),
        ]

        for method, url, payload in protected_requests:
            with self.subTest(method=method, url=url):
                response = getattr(self.client, method)(url, payload, format="json") if payload is not None else getattr(self.client, method)(url)
                self.assertEqual(response.status_code, 403)

    def test_catalog_reads_and_csrf_bootstrap_remain_public(self):
        for url in ("/api/auth/csrf/", "/api/catalog/categories/", "/api/catalog/products/"):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)
