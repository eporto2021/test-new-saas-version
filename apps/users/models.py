import hashlib
import uuid
from functools import cached_property

from allauth.account.models import EmailAddress
from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.subscriptions.models import SubscriptionModelBase
from apps.users.helpers import validate_profile_picture


def _get_avatar_filename(instance, filename):
    """Use random filename prevent overwriting existing files & to fix caching issues."""
    return f"profile-pictures/{uuid.uuid4()}.{filename.split('.')[-1]}"


class Software(models.Model):
    """
    Represents a software/tool that users might use in their business.
    """
    name = models.CharField(max_length=100, unique=True)
    icon = models.CharField(max_length=200, help_text="Font Awesome icon class (e.g., 'fa-route' for route optimization)")
    category = models.CharField(max_length=100, blank=True, help_text="Category like 'Route Planning', 'Accounting', etc.")
    order = models.IntegerField(default=0, help_text="Display order")
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = "Software"
    
    def __str__(self):
        return self.name


class CustomUser(SubscriptionModelBase, AbstractUser):
    """
    Add additional fields to the user model here.
    """

    avatar = models.FileField(upload_to=_get_avatar_filename, blank=True, validators=[validate_profile_picture])
    language = models.CharField(max_length=10, blank=True, null=True)
    timezone = models.CharField(max_length=100, blank=True, default="")
    software_tools = models.ManyToManyField(Software, blank=True, related_name='users')
    custom_software = models.TextField(blank=True, help_text="Custom software tools not in the predefined list")
    completed_software_survey = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.get_full_name()} <{self.email or self.username}>"

    def get_display_name(self) -> str:
        if self.get_full_name().strip():
            return self.get_full_name()
        return self.email or self.username

    @property
    def avatar_url(self) -> str:
        if self.avatar:
            return self.avatar.url
        else:
            return f"https://www.gravatar.com/avatar/{self.gravatar_id}?s=128&d=identicon"

    @property
    def gravatar_id(self) -> str:
        # https://en.gravatar.com/site/implement/hash/
        return hashlib.md5(self.email.lower().strip().encode("utf-8")).hexdigest()

    @cached_property
    def has_verified_email(self):
        return EmailAddress.objects.filter(user=self, verified=True).exists()
