from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser, Software


@admin.register(Software)
class SoftwareAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "icon", "order", "is_active")
    list_filter = ("category", "is_active")
    list_editable = ("order", "is_active")
    search_fields = ("name", "category")


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = UserAdmin.list_display + ("date_joined", "subscription", "completed_software_survey")
    list_filter = UserAdmin.list_filter + ("date_joined", "completed_software_survey")
    ordering = ("-date_joined",)

    fieldsets = UserAdmin.fieldsets + (
        ("Custom Fields", {"fields": ("avatar", "subscription", "customer", "language", "timezone", "software_tools", "custom_software", "completed_software_survey")}),
    )
    filter_horizontal = ("software_tools",)
