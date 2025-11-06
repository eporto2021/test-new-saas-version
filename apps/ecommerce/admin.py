from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import ProductConfiguration, Purchase


@admin.register(ProductConfiguration)
class ProductConfigurationAdmin(admin.ModelAdmin):
    list_display = ["slug", "product", "created_at", "is_active", "has_content"]

    def has_content(self, obj):
        return bool(obj.content)

    has_content.boolean = True
    has_content.short_description = _("Has Content")


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ["product", "product_configuration__product", "user", "created_at", "is_valid"]
    list_filter = ["product", "user", "created_at", "is_valid"]
