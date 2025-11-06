"""
Tests for file_filters template tags and new service views.
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.template import Template, Context
from django.core.files.uploadedfile import SimpleUploadedFile
import json

from apps.services.models import Service, UserDataFile
from apps.subscriptions.models import SubscriptionAvailability
from djstripe.models import Product, Price
from djstripe import enums

User = get_user_model()


class FileFiltersTemplateTagsTests(TestCase):
    """Test the file_filters template tag library."""

    def test_filename_filter(self):
        """Test the filename filter extracts filename correctly."""
        template_code = "{% load file_filters %}{{ 'path/to/file.txt'|filename }}"
        
        template = Template(template_code)
        context = Context({})
        result = template.render(context)
        
        self.assertEqual(result, "file.txt")

    def test_file_extension_filter(self):
        """Test the file_extension filter extracts extension correctly."""
        template_code = "{% load file_filters %}{{ 'file.txt'|file_extension }}"
        
        template = Template(template_code)
        context = Context({})
        result = template.render(context)
        
        self.assertEqual(result, ".txt")

    def test_file_size_human_filter(self):
        """Test the file_size_human filter formats sizes correctly."""
        template_code = "{% load file_filters %}{{ 1024|file_size_human }}"
        
        template = Template(template_code)
        context = Context({})
        result = template.render(context)
        
        self.assertEqual(result, "1.0 KB")

    def test_file_size_human_with_invalid_input(self):
        """Test file_size_human filter handles invalid input gracefully."""
        template_code = "{% load file_filters %}{{ 'invalid'|file_size_human }}"
        
        template = Template(template_code)
        context = Context({})
        result = template.render(context)
        
        self.assertEqual(result, "0 B")


class ServiceViewsTests(TestCase):
    """Test the new service views for file processing."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser@example.com",
            email="testuser@example.com",
            password="testpass123"
        )
        self.client = Client()
        self.client.login(username="testuser@example.com", password="testpass123")

        # Create a test Stripe product for subscription
        self.stripe_product = Product.objects.create(
            id="prod_test_service",
            name="Test Service Product",
            description="A product for testing service",
            active=True
        )
        
        self.stripe_price = Price.objects.create(
            id="price_test_service",
            product=self.stripe_product,
            currency="usd",
            unit_amount=1000,
            active=True,
            type=enums.PriceType.recurring,
            recurring={"interval": "month", "interval_count": 1}
        )
        
        self.stripe_product.default_price = self.stripe_price
        self.stripe_product.save()

        # Create a test service
        self.service = Service.objects.create(
            name="Test Service",
            slug="test-service",
            description="A test service",
            stripe_product=self.stripe_product,
            is_active=True
        )

        # Create subscription availability
        SubscriptionAvailability.objects.create(
            stripe_product=self.stripe_product,
            user=self.user,
            make_subscription_available=True
        )

        # Create a test file
        self.test_file = SimpleUploadedFile(
            "test.csv",
            b"name,email\nJohn,john@example.com",
            content_type="text/csv"
        )

    def test_process_data_file_view_success(self):
        """Test successful file processing."""
        # Create a test data file
        data_file = UserDataFile.objects.create(
            user=self.user,
            service=self.service,
            file=self.test_file,
            original_filename="test.csv",
            file_type="csv",
            processing_status="pending"
        )

        # Test the process endpoint
        response = self.client.post(
            reverse('services:process_data_file', args=['test-service']),
            data=json.dumps({'file_id': data_file.id}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['message'], 'Processing started')

    def test_process_data_file_view_file_not_found(self):
        """Test process endpoint with non-existent file."""
        response = self.client.post(
            reverse('services:process_data_file', args=['test-service']),
            data=json.dumps({'file_id': 99999}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('File not found', data['error'])

    def test_process_data_file_view_missing_file_id(self):
        """Test process endpoint without file_id."""
        response = self.client.post(
            reverse('services:process_data_file', args=['test-service']),
            data=json.dumps({}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('File ID is required', data['error'])

    def test_delete_data_file_view_success(self):
        """Test successful file deletion."""
        # Create a test data file
        data_file = UserDataFile.objects.create(
            user=self.user,
            service=self.service,
            file=self.test_file,
            original_filename="test.csv",
            file_type="csv",
            processing_status="pending"
        )

        # Test the delete endpoint
        response = self.client.post(
            reverse('services:delete_data_file', args=['test-service']),
            data=json.dumps({'file_id': data_file.id}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['message'], 'File deleted successfully')

        # Verify file was deleted
        self.assertFalse(UserDataFile.objects.filter(id=data_file.id).exists())

    def test_delete_data_file_view_file_not_found(self):
        """Test delete endpoint with non-existent file."""
        response = self.client.post(
            reverse('services:delete_data_file', args=['test-service']),
            data=json.dumps({'file_id': 99999}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('File not found', data['error'])

    def test_process_all_files_view_success(self):
        """Test successful processing of all pending files."""
        # Create multiple pending files
        for i in range(3):
            UserDataFile.objects.create(
                user=self.user,
                service=self.service,
                file=self.test_file,
                original_filename=f"test{i}.csv",
                file_type="csv",
                processing_status="pending"
            )

        # Test the process all endpoint
        response = self.client.post(
            reverse('services:process_all_files', args=['test-service']),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['file_count'], 3)
        self.assertIn('Processing started for 3 file(s)', data['message'])

    def test_process_all_files_view_no_pending_files(self):
        """Test process all endpoint with no pending files."""
        response = self.client.post(
            reverse('services:process_all_files', args=['test-service']),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('No pending files to process', data['error'])

    def test_delete_all_files_view_success(self):
        """Test successful deletion of all files."""
        # Create multiple files
        for i in range(3):
            UserDataFile.objects.create(
                user=self.user,
                service=self.service,
                file=self.test_file,
                original_filename=f"test{i}.csv",
                file_type="csv",
                processing_status="pending"
            )

        # Test the delete all endpoint
        response = self.client.post(
            reverse('services:delete_all_files', args=['test-service']),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['deleted_count'], 3)
        self.assertIn('Successfully deleted 3 file(s)', data['message'])

        # Verify all files were deleted
        self.assertEqual(UserDataFile.objects.filter(user=self.user).count(), 0)

    def test_delete_all_files_view_no_files(self):
        """Test delete all endpoint with no files."""
        response = self.client.post(
            reverse('services:delete_all_files', args=['test-service']),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('No files to delete', data['error'])

    def test_views_require_authentication(self):
        """Test that all views require authentication."""
        self.client.logout()
        
        endpoints = [
            ('services:process_data_file', {'file_id': 1}),
            ('services:delete_data_file', {'file_id': 1}),
            ('services:process_all_files', {}),
            ('services:delete_all_files', {}),
        ]
        
        for endpoint_name, data in endpoints:
            with self.subTest(endpoint=endpoint_name):
                response = self.client.post(
                    reverse(endpoint_name, args=['test-service']),
                    data=json.dumps(data),
                    content_type='application/json'
                )
                # Should redirect to login page
                self.assertEqual(response.status_code, 302)

    def test_views_require_post_method(self):
        """Test that all views require POST method."""
        endpoints = [
            'services:process_data_file',
            'services:delete_data_file', 
            'services:process_all_files',
            'services:delete_all_files',
        ]
        
        for endpoint_name in endpoints:
            with self.subTest(endpoint=endpoint_name):
                response = self.client.get(
                    reverse(endpoint_name, args=['test-service'])
                )
                self.assertEqual(response.status_code, 405)  # Method Not Allowed

    def test_user_can_only_access_own_files(self):
        """Test that users can only access their own files."""
        # Create another user and file
        other_user = User.objects.create_user(
            username="other@example.com",
            email="other@example.com",
            password="testpass123"
        )
        
        other_file = UserDataFile.objects.create(
            user=other_user,
            service=self.service,
            file=self.test_file,
            original_filename="other.csv",
            file_type="csv",
            processing_status="pending"
        )

        # Try to process the other user's file
        response = self.client.post(
            reverse('services:process_data_file', args=['test-service']),
            data=json.dumps({'file_id': other_file.id}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('File not found', data['error'])

    def test_invalid_json_handling(self):
        """Test that views handle invalid JSON gracefully."""
        response = self.client.post(
            reverse('services:process_data_file', args=['test-service']),
            data="invalid json",
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('Invalid JSON', data['error'])
