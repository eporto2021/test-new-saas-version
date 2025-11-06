from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from djstripe.models import Price, Product

from apps.ecommerce.models import ProductConfiguration, Purchase
from apps.users.models import CustomUser
from apps.web.tests.base import TEST_STORAGES


@override_settings(STORAGES=TEST_STORAGES)
class TestDigitalDownloads(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(username="test@example.com", password="testpass")
        self.other_user = CustomUser.objects.create_user(username="other@example.com", password="testpass")

        # Create a stripe product and price (mock data for testing)
        self.stripe_product = Product.objects.create(
            id="prod_test123", name="Test Digital Product", description="A test product with digital content"
        )
        self.stripe_price = Price.objects.create(
            id="price_test123",
            product=self.stripe_product,
            currency="usd",
            unit_amount=1000,  # $10.00
            active=True,
        )

        # Create product configuration
        self.product_config = ProductConfiguration.objects.create(
            slug="test-digital-product",
            product=self.stripe_product,
            is_active=True,
            overview="Test digital product overview",
        )

        # Create a test file
        self.test_file_content = b"Test digital content"
        self.test_file = SimpleUploadedFile("test_file.pdf", self.test_file_content, content_type="application/pdf")

        # Create valid purchase for user
        self.purchase = Purchase.objects.create(
            user=self.user,
            product_configuration=self.product_config,
            product=self.stripe_product,
            price=self.stripe_price,
            checkout_session_id="cs_test123",
            is_valid=True,
        )

    def test_download_view_requires_login(self):
        """Test that download view requires authentication"""
        self.product_config.content = self.test_file
        self.product_config.save()

        url = reverse("ecommerce:download_product_file", args=[self.product_config.slug])
        response = self.client.get(url)
        self.assertRedirects(response, f"/accounts/login/?next={url}")

    def test_download_view_requires_purchase(self):
        """Test that download view requires valid purchase"""
        self.product_config.content = self.test_file
        self.product_config.save()

        self.client.login(username="other@example.com", password="testpass")
        url = reverse("ecommerce:download_product_file", args=[self.product_config.slug])
        response = self.client.get(url)
        # Should redirect to ecommerce home with error message
        self.assertRedirects(response, reverse("ecommerce:ecommerce_home"))

    def test_download_view_404_when_no_file(self):
        """Test that download view returns 404 when no digital file exists"""
        self.client.login(username="test@example.com", password="testpass")
        url = reverse("ecommerce:download_product_file", args=[self.product_config.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_successful_download_with_valid_purchase(self):
        """Test successful file download with valid purchase"""
        self.product_config.content = self.test_file
        self.product_config.save()

        self.client.login(username="test@example.com", password="testpass")
        url = reverse("ecommerce:download_product_file", args=[self.product_config.slug])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(response.has_header("Content-Disposition"))
        self.assertIn("attachment", response["Content-Disposition"])
        # Django adds a random suffix to uploaded files, so we check for the base name pattern
        self.assertRegex(response["Content-Disposition"], r'filename="test_file.*\.pdf"')

    def test_access_product_shows_download_link(self):
        """Test that access product page shows download link when file exists"""
        self.product_config.content = self.test_file
        self.product_config.save()

        self.client.login(username="test@example.com", password="testpass")
        url = reverse("ecommerce:access_product", args=[self.product_config.slug])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Download File")
        download_url = reverse("ecommerce:download_product_file", args=[self.product_config.slug])
        self.assertContains(response, download_url)

    def test_access_product_no_download_link_without_file(self):
        """Test that access product page doesn't show download link when no file exists"""
        self.client.login(username="test@example.com", password="testpass")
        url = reverse("ecommerce:access_product", args=[self.product_config.slug])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Download File")
