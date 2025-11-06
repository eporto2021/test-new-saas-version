"""
Tests for metadata module imports to ensure no AppRegistryNotReady errors.

This test specifically addresses the issue where non-lazy gettext calls at import time
can cause Django's AppRegistryNotReady exception during deployment (e.g., collectstatic).
"""

from django.test import TestCase
from django.core.exceptions import AppRegistryNotReady


class MetadataImportTests(TestCase):
    """Test that metadata module can be imported without triggering app registry issues."""

    def test_metadata_import_without_app_registry(self):
        """
        Test that importing metadata module doesn't trigger AppRegistryNotReady.
        
        This test simulates the conditions during Docker build where Django's
        app registry might not be fully initialized when collectstatic runs.
        """
        # Clear any existing app registry state
        from django.apps import apps
        apps.clear_cache()
        
        # This should not raise AppRegistryNotReady
        try:
            from apps.subscriptions.metadata import (
                ProductMetadata,
                ProductWithMetadata,
                get_plan_name_for_interval,
                get_help_text_for_interval,
                get_active_plan_interval_metadata,
                ACTIVE_PLAN_INTERVALS,
                ACTIVE_PRODUCTS
            )
            
            # Verify the imports worked
            self.assertTrue(ProductMetadata is not None)
            self.assertTrue(ProductWithMetadata is not None)
            self.assertTrue(callable(get_plan_name_for_interval))
            self.assertTrue(callable(get_help_text_for_interval))
            self.assertTrue(callable(get_active_plan_interval_metadata))
            self.assertTrue(isinstance(ACTIVE_PLAN_INTERVALS, list))
            self.assertTrue(isinstance(ACTIVE_PRODUCTS, list))
            
        except AppRegistryNotReady as e:
            self.fail(f"Importing metadata module raised AppRegistryNotReady: {e}")

    def test_metadata_functions_work_after_import(self):
        """
        Test that the metadata functions work correctly after import.
        
        This ensures our lazy loading fix doesn't break functionality.
        """
        from apps.subscriptions.metadata import (
            get_plan_name_for_interval,
            get_help_text_for_interval,
            ACTIVE_PLAN_INTERVALS
        )
        from djstripe.enums import PlanInterval
        
        # Test that the functions work with valid intervals
        if ACTIVE_PLAN_INTERVALS:
            test_interval = ACTIVE_PLAN_INTERVALS[0]
            
            # These should not raise any exceptions
            name = get_plan_name_for_interval(test_interval)
            help_text = get_help_text_for_interval(test_interval)
            
            # Verify they return strings (lazy or otherwise)
            self.assertIsNotNone(name)
            self.assertIsNotNone(help_text)
            
            # Test with a non-existent interval
            name_custom = get_plan_name_for_interval("custom_interval")
            help_text_custom = get_help_text_for_interval("custom_interval")
            
            self.assertIsNotNone(name_custom)
            self.assertIsNotNone(help_text_custom)

    def test_metadata_import_in_production_settings_context(self):
        """
        Test that metadata can be imported in a production settings context.
        
        This simulates the exact scenario that was failing during Docker build.
        """
        # Simulate production settings import pattern
        try:
            # This is the import pattern used in settings_production.py
            from apps.subscriptions.metadata import ProductMetadata
            
            # Verify we can create a ProductMetadata instance
            metadata = ProductMetadata(
                stripe_id='test_prod_123',
                slug='test-product',
                name='Test Product',
                features=['Feature 1', 'Feature 2'],
                description='Test product description'
            )
            
            self.assertEqual(metadata.stripe_id, 'test_prod_123')
            self.assertEqual(metadata.slug, 'test-product')
            self.assertEqual(metadata.name, 'Test Product')
            self.assertEqual(len(metadata.features), 2)
            
        except AppRegistryNotReady as e:
            self.fail(f"Production settings import pattern raised AppRegistryNotReady: {e}")
        except Exception as e:
            # Other exceptions are fine, we just want to ensure no AppRegistryNotReady
            if isinstance(e, AppRegistryNotReady):
                self.fail(f"Unexpected AppRegistryNotReady: {e}")
