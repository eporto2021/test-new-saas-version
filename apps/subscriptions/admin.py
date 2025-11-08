from django.contrib import admin
from django.utils.html import format_html
from .models import SubscriptionRequest, SubscriptionAvailability, ProductDemoLink
from apps.users.models import CustomUser


@admin.register(SubscriptionRequest)
class SubscriptionRequestAdmin(admin.ModelAdmin):
    list_display = ['user_info', 'product_name', 'status_display', 'created_at', 'view_user_link']
    list_filter = ['status', 'created_at', 'user__is_staff', 'user__is_superuser']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'product_name', 'product_stripe_id']
    readonly_fields = ['created_at', 'updated_at', 'product_info']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        ('Request Information', {
            'fields': ('user', 'product_name', 'product_stripe_id', 'message', 'status'),
            'description': 'When status is set to "Approved", the user will see a "Subscribe" button for this product.'
        }),
        ('Admin Notes', {
            'fields': ('admin_notes',),
            'description': 'Internal notes for tracking approval decisions and follow-up actions.'
        }),
        ('Product Details', {
            'fields': ('product_info',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_info(self, obj):
        """Display user information with better formatting"""
        full_name = obj.user.get_full_name()
        if full_name:
            return f"{full_name} ({obj.user.email})"
        return obj.user.email
    user_info.short_description = 'User'
    user_info.admin_order_field = 'user__email'
    
    def status_display(self, obj):
        """Display status with colored indicators"""
        status_colors = {
            'pending': 'orange',
            'contacted': 'blue', 
            'approved': 'green',
            'rejected': 'red'
        }
        status_icons = {
            'pending': '⏳',
            'contacted': '📞',
            'approved': '✅',
            'rejected': '❌'
        }
        color = status_colors.get(obj.status, 'black')
        icon = status_icons.get(obj.status, '')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color, icon, obj.get_status_display()
        )
    status_display.short_description = 'Status'
    status_display.admin_order_field = 'status'
    
    def view_user_link(self, obj):
        """Link to view the user in admin"""
        from django.urls import reverse
        url = reverse('admin:users_customuser_change', args=[obj.user.id])
        return format_html('<a href="{}">👤 View Profile</a>', url)
    view_user_link.short_description = 'User Profile'
    
    def product_info(self, obj):
        """Display detailed product information"""
        if obj.pk:  # Only for existing objects
            try:
                from djstripe.models import Product
                product = Product.objects.get(id=obj.product_stripe_id)
                return format_html(
                    '<div style="background: #f8f9fa; padding: 10px; border-radius: 5px;">'
                    '<strong>Product:</strong> {}<br>'
                    '<strong>Stripe ID:</strong> {}<br>'
                    '<strong>Active:</strong> {}<br>'
                    '<strong>Description:</strong> {}'
                    '</div>',
                    product.name,
                    product.id,
                    'Yes' if product.active else 'No',
                    product.description or 'No description'
                )
            except Product.DoesNotExist:
                return format_html(
                    '<div style="background: #fff3cd; padding: 10px; border-radius: 5px; color: #856404;">'
                    '⚠️ Product not found in Stripe. ID: {}'
                    '</div>',
                    obj.product_stripe_id
                )
        return 'Product information will appear after saving.'
    product_info.short_description = 'Product Details'
    
    actions = ['mark_contacted', 'mark_approved', 'mark_rejected', 'approve_and_enable_subscription']
    
    def mark_contacted(self, request, queryset):
        updated = queryset.update(status='contacted')
        self.message_user(request, f'{updated} requests marked as contacted.')
    mark_contacted.short_description = '📞 Mark as contacted'
    
    def mark_approved(self, request, queryset):
        updated_count = 0
        for subscription_request in queryset:
            # Update the request status
            subscription_request.status = 'approved'
            subscription_request.save()
            
            # Create or update SubscriptionAvailability to enable subscription
            from djstripe.models import Product
            try:
                product = Product.objects.get(id=subscription_request.product_stripe_id)
                SubscriptionAvailability.objects.update_or_create(
                    stripe_product=product,
                    user=subscription_request.user,
                    defaults={'make_subscription_available': True}
                )
                updated_count += 1
            except Product.DoesNotExist:
                self.message_user(
                    request, 
                    f'Warning: Product {subscription_request.product_stripe_id} not found in Stripe for request {subscription_request.id}',
                    level='warning'
                )
        
        self.message_user(request, f'{updated_count} requests approved and subscription enabled! Users can now see the Subscribe button.')
    mark_approved.short_description = '✅ Approve requests (enable subscription)'
    
    def mark_rejected(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} requests marked as rejected.')
    mark_rejected.short_description = '❌ Reject requests'
    
    def approve_and_enable_subscription(self, request, queryset):
        """Special action that approves requests and provides additional info"""
        # Use the same logic as mark_approved
        self.mark_approved(request, queryset)
    approve_and_enable_subscription.short_description = '🚀 Approve & Enable Subscription'


@admin.register(SubscriptionAvailability)
class SubscriptionAvailabilityAdmin(admin.ModelAdmin):
    list_display = ['product_name', 'user_display', 'availability_status', 'scope', 'updated_at']
    list_filter = ['make_subscription_available', 'created_at', 'user__is_staff', 'user__is_superuser']
    search_fields = ['stripe_product__name', 'stripe_product__id', 'user__email', 'user__username', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at', 'product_info']
    ordering = ['stripe_product__name', 'user__email']
    
    fieldsets = (
        ('Product Information', {
            'fields': ('product_info', 'stripe_product', 'user'),
            'description': 'Select the Stripe product and user. Leave user blank for global settings.'
        }),
        ('Availability Settings', {
            'fields': ('make_subscription_available',),
            'description': 'When checked, users will see a "Subscribe" button. When unchecked, they will see a "Request Subscription" button.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('stripe_product', 'user')
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "user":
            kwargs["queryset"] = CustomUser.objects.all().order_by('email')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def product_name(self, obj):
        """Display product name with better formatting"""
        return obj.stripe_product.name
    product_name.short_description = 'Product'
    product_name.admin_order_field = 'stripe_product__name'
    
    def user_display(self, obj):
        """Display user information or 'Global'"""
        if obj.user:
            return f"{obj.user.get_full_name() or obj.user.username} ({obj.user.email})"
        return format_html('<strong>Global</strong>')
    user_display.short_description = 'User'
    user_display.admin_order_field = 'user__email'
    
    def availability_status(self, obj):
        """Display availability status with colored indicators"""
        if obj.make_subscription_available:
            return format_html('<span style="color: green; font-weight: bold;">✓ Available</span>')
        else:
            return format_html('<span style="color: orange; font-weight: bold;">⚠ Request Only</span>')
    availability_status.short_description = 'Status'
    availability_status.admin_order_field = 'make_subscription_available'
    
    def scope(self, obj):
        """Display whether this is user-specific or global"""
        if obj.user:
            return format_html('<span style="color: blue;">User-Specific</span>')
        else:
            return format_html('<span style="color: purple;">Global</span>')
    scope.short_description = 'Scope'
    
    def product_info(self, obj):
        """Display detailed product information"""
        if obj.pk:  # Only for existing objects
            return format_html(
                '<div style="background: #f8f9fa; padding: 10px; border-radius: 5px;">'
                '<strong>Product:</strong> {}<br>'
                '<strong>Stripe ID:</strong> {}<br>'
                '<strong>Active:</strong> {}'
                '</div>',
                obj.stripe_product.name,
                obj.stripe_product.id,
                'Yes' if obj.stripe_product.active else 'No'
            )
        return 'Product information will appear after saving.'
    product_info.short_description = 'Product Details'
    
    actions = ['make_available', 'make_request_only', 'create_for_all_users']
    
    def make_available(self, request, queryset):
        """Bulk action to make subscriptions available"""
        updated = queryset.update(make_subscription_available=True)
        self.message_user(request, f'{updated} subscription(s) marked as available.')
    make_available.short_description = 'Make selected subscriptions available'
    
    def make_request_only(self, request, queryset):
        """Bulk action to make subscriptions request-only"""
        updated = queryset.update(make_subscription_available=False)
        self.message_user(request, f'{updated} subscription(s) marked as request-only.')
    make_request_only.short_description = 'Make selected subscriptions request-only'
    
    def create_for_all_users(self, request, queryset):
        """Create availability records for all users for selected products"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        created_count = 0
        for availability in queryset:
            if availability.user:  # Only process user-specific records
                continue
                
            # Create availability records for all users
            for user in User.objects.all():
                obj, created = SubscriptionAvailability.objects.get_or_create(
                    stripe_product=availability.stripe_product,
                    user=user,
                    defaults={'make_subscription_available': False}
                )
                if created:
                    created_count += 1
        
        self.message_user(request, f'Created {created_count} user-specific availability records.')
    create_for_all_users.short_description = 'Create user-specific records for all users'


@admin.register(ProductDemoLink)
class ProductDemoLinkAdmin(admin.ModelAdmin):
    list_display = ['product_name', 'stripe_product_id', 'demo_link_display', 'is_active', 'button_text', 'display_order', 'updated_at']
    list_filter = ['is_active', 'open_in_new_tab', 'created_at']
    search_fields = ['product_name', 'stripe_product_id', 'demo_url', 'button_text']
    readonly_fields = ['created_at', 'updated_at', 'preview_link']
    ordering = ['display_order', 'product_name']
    
    fieldsets = (
        ('Product Information', {
            'fields': ('product_name', 'stripe_product_id'),
            'description': 'Enter the product name and Stripe Product ID (e.g., prod_T9FO1AD2u8s2xX)'
        }),
        ('Demo Link Settings', {
            'fields': ('demo_url', 'button_text', 'open_in_new_tab', 'is_active'),
            'description': 'Configure the demo link button that appears on the product card'
        }),
        ('Display Settings', {
            'fields': ('display_order', 'preview_link'),
            'description': 'Control the display order and preview the link'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def demo_link_display(self, obj):
        """Display the demo URL as a clickable link"""
        if obj.demo_url:
            target = '_blank' if obj.open_in_new_tab else '_self'
            return format_html(
                '<a href="{}" target="{}" style="color: #3b82f6;">🔗 {}</a>',
                obj.demo_url, target, obj.demo_url[:50] + '...' if len(obj.demo_url) > 50 else obj.demo_url
            )
        return '-'
    demo_link_display.short_description = 'Demo URL'
    
    def preview_link(self, obj):
        """Preview how the button will appear"""
        if obj.pk:
            active_badge = '✅ Active' if obj.is_active else '⚠️ Inactive'
            target_badge = '🔗 New Tab' if obj.open_in_new_tab else '🔗 Same Tab'
            return format_html(
                '<div style="background: #f8f9fa; padding: 15px; border-radius: 8px; border: 1px solid #e5e7eb;">'
                '<div style="margin-bottom: 10px;">'
                '<span style="background: {}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px; margin-right: 5px;">{}</span>'
                '<span style="background: #6366f1; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px;">{}</span>'
                '</div>'
                '<strong>Button Preview:</strong><br>'
                '<a href="{}" target="{}" '
                'style="display: inline-block; margin-top: 10px; padding: 8px 16px; background: #3b82f6; color: white; '
                'text-decoration: none; border-radius: 6px; font-weight: 600; cursor: pointer;">'
                '{}'
                '</a>'
                '</div>',
                '#10b981' if obj.is_active else '#f59e0b',
                active_badge,
                target_badge,
                obj.demo_url,
                '_blank' if obj.open_in_new_tab else '_self',
                obj.button_text
            )
        return 'Preview will appear after saving.'
    preview_link.short_description = 'Button Preview'
    
    actions = ['activate_demos', 'deactivate_demos']
    
    def activate_demos(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} demo link(s) activated.')
    activate_demos.short_description = '✅ Activate selected demo links'
    
    def deactivate_demos(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} demo link(s) deactivated.')
    deactivate_demos.short_description = '⚠️ Deactivate selected demo links'
