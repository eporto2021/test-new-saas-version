"""
Custom template tags for Vite integration that work with network access.
"""
from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

register = template.Library()


def get_vite_dev_server_url(request):
    """Get the Vite dev server URL based on the request host."""
    if not request:
        return 'http://localhost:5173'
    
    request_host = request.get_host().split(':')[0]
    
    if request_host in ('127.0.0.1', 'localhost'):
        return 'http://localhost:5173'
    else:
        return f'http://{request_host}:5173'


@register.simple_tag(takes_context=True)
def vite_hmr_client_network(context):
    """
    Custom Vite HMR client tag that uses the request host instead of hardcoded localhost.
    This allows HMR to work when accessing the app via network IP.
    """
    request = context.get('request')
    vite_url = get_vite_dev_server_url(request)
    
    # Generate the HMR client script tag (simplified version that works with network access)
    # Use mark_safe so the HTML is rendered, not escaped as text
    script_tag = f'<script type="module" src="{vite_url}/@vite/client"></script>'
    return mark_safe(script_tag)


@register.simple_tag(takes_context=True)
def vite_asset_url_network(context, path):
    """
    Custom vite_asset_url tag that uses the request host for dev mode.
    This ensures CSS and other assets load correctly when accessing via network IP.
    """
    from django_vite.templatetags.django_vite import vite_asset_url as django_vite_asset_url
    
    # In dev mode, we need to use the request host
    if settings.DEBUG and hasattr(settings, 'DJANGO_VITE'):
        djv_config = settings.DJANGO_VITE.get('default', {})
        if djv_config.get('dev_mode', False):
            request = context.get('request')
            if request:
                vite_url = get_vite_dev_server_url(request)
                # Return the dev server URL for the asset
                # Vite serves assets from /static/ in dev mode
                return f'{vite_url}/static/{path}'
    
    # Fallback to django-vite's default behavior (production mode)
    try:
        return django_vite_asset_url(context, path)
    except Exception:
        # If django-vite fails, return a fallback
        return f'/static/{path}'

