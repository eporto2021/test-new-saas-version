from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from djstripe.models import Product, Subscription
from django.core.files.storage import default_storage
from datetime import datetime

from apps.subscriptions.models import SubscriptionModelBase
from apps.users.models import CustomUser


def user_data_file_upload_path(instance, filename):
    """Generate upload path for user data files"""
    return f'user_data/user_{instance.user.id}/{datetime.now().strftime("%Y/%m/%d")}/{filename}'


def processed_data_file_upload_path(instance, filename):
    """Generate upload path for processed data files"""
    return f'processed_data/user_{instance.data_file.user.id}/{datetime.now().strftime("%Y/%m/%d")}/{filename}'


class Service(models.Model):
    """
    Represents a software service that users can subscribe to.
    Each service corresponds to a Stripe product.
    """
    
    name = models.CharField(max_length=100, help_text=_("Display name of the service"))
    slug = models.SlugField(max_length=150, unique=True, help_text=_("URL-friendly identifier"))
    description = models.TextField(blank=True, help_text=_("Description of what this service provides"))
    stripe_product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        help_text=_("The Stripe product that grants access to this service")
    )
    icon = models.CharField(
        max_length=200, 
        default="fa-solid fa-cube", 
        help_text=_("Font Awesome icon class for this service")
    )
    is_active = models.BooleanField(default=True, help_text=_("Whether this service is available for subscription"))
    order = models.PositiveIntegerField(default=0, help_text=_("Display order in navigation"))
    
    class Meta:
        ordering = ['order', 'name']
        verbose_name = _("Service")
        verbose_name_plural = _("Services")
    
    def __str__(self):
        return self.name


class UserServiceAccess(models.Model):
    """
    Tracks which services a user has access to based on their subscriptions.
    """
    
    user = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE,
        related_name='service_accesses'
    )
    service = models.ForeignKey(
        Service, 
        on_delete=models.CASCADE,
        related_name='user_accesses'
    )
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text=_("The subscription that grants this access")
    )
    granted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text=_("When this access expires (if applicable)")
    )
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['user', 'service']
        verbose_name = _("User Service Access")
        verbose_name_plural = _("User Service Accesses")
    
    def __str__(self):
        return f"{self.user.email} - {self.service.name}"
    
    @property
    def is_valid(self):
        """Check if this access is still valid"""
        if not self.is_active:
            return False
        return not (self.expires_at and self.expires_at < timezone.now())


class UserDataFile(models.Model):
    """
    Stores user-uploaded data files for processing by their custom logic.
    """
    
    PROCESSING_STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('processing', _('Processing')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
    ]
    
    user = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE,
        related_name='data_files'
    )
    service = models.ForeignKey(
        Service, 
        on_delete=models.CASCADE,
        related_name='user_data_files'
    )
    file = models.FileField(
        upload_to=user_data_file_upload_path,
        help_text=_("The uploaded data file")
    )
    original_filename = models.CharField(
        max_length=255,
        help_text=_("Original filename when uploaded")
    )
    file_type = models.CharField(
        max_length=50,
        help_text=_("File type (csv, json, xlsx, etc.)")
    )
    processing_status = models.CharField(
        max_length=20,
        choices=PROCESSING_STATUS_CHOICES,
        default='pending'
    )
    processing_log = models.TextField(
        blank=True,
        help_text=_("Log of processing steps and any errors")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = _("User Data File")
        verbose_name_plural = _("User Data Files")
    
    def __str__(self):
        return f"{self.user.email} - {self.original_filename} ({self.service.name})"
    
    @property
    def file_size(self):
        """Get file size in bytes"""
        try:
            return self.file.size
        except (ValueError, OSError):
            return 0
    
    @property
    def file_size_human(self):
        """Get human-readable file size"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"


class UserProcessedData(models.Model):
    """
    Stores the results of processing user data files.
    """
    
    data_file = models.OneToOneField(
        UserDataFile,
        on_delete=models.CASCADE,
        related_name='processed_data'
    )
    processed_file = models.FileField(
        upload_to=processed_data_file_upload_path,
        help_text=_("The processed/cleaned data file")
    )
    summary_data = models.JSONField(
        default=dict,
        help_text=_("Summary statistics and metadata about the processed data")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _("User Processed Data")
        verbose_name_plural = _("User Processed Data")
    
    def __str__(self):
        return f"Processed data for {self.data_file.original_filename}"
