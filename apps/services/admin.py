from django.contrib import admin
from .models import Service, UserServiceAccess, UserDataFile, UserProcessedData


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'stripe_product', 'is_active', 'order']
    list_filter = ['is_active']
    search_fields = ['name', 'slug', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['order', 'name']


@admin.register(UserServiceAccess)
class UserServiceAccessAdmin(admin.ModelAdmin):
    list_display = ['user', 'service', 'subscription', 'is_active', 'granted_at', 'is_valid']
    list_filter = ['is_active', 'service']
    search_fields = ['user__email', 'service__name']
    readonly_fields = ['granted_at']
    
    def is_valid(self, obj):
        return obj.is_valid
    is_valid.boolean = True


@admin.register(UserDataFile)
class UserDataFileAdmin(admin.ModelAdmin):
    list_display = [
        'original_filename', 'user', 'service', 'file_type',
        'processing_status', 'file_size_human', 'created_at'
    ]
    list_filter = ['processing_status', 'file_type', 'service', 'created_at']
    search_fields = ['original_filename', 'user__email', 'service__name']
    readonly_fields = ['created_at', 'processed_at', 'file_size_human']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('File Information', {
            'fields': ('user', 'service', 'file', 'original_filename', 'file_type', 'file_size_human')
        }),
        ('Processing Status', {
            'fields': ('processing_status', 'processing_log', 'processed_at')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )


@admin.register(UserProcessedData)
class UserProcessedDataAdmin(admin.ModelAdmin):
    list_display = ['data_file', 'created_at']
    search_fields = ['data_file__original_filename', 'data_file__user__email']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
