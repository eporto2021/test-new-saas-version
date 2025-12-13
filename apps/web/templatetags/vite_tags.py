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
    
    In dev mode: expects source paths (e.g., 'assets/styles/site-base.css')
    In production: can use entry names (e.g., 'site-base-css') or source paths
    """
    from django_vite.templatetags.django_vite import vite_asset_url as django_vite_asset_url
    
    # Mapping from entry names to source paths (for dev mode)
    ENTRY_TO_SOURCE = {
        'site-base-css': 'assets/styles/site-base.css',
        'site-tailwind-css': 'assets/styles/site-tailwind.css',
        'site': 'assets/javascript/site.js',
        'app': 'assets/javascript/app.js',
        'pegasus': 'assets/javascript/pegasus/pegasus.js',
        'react-object-lifecycle': 'assets/javascript/pegasus/examples/react/react-object-lifecycle.jsx',
        'vue-object-lifecycle': 'assets/javascript/pegasus/examples/vue/vue-object-lifecycle.js',
        'chat-ws-initialize': 'assets/javascript/chat/ws_initialize.ts',
    }
    
    # Reverse mapping from source paths to entry names (for production manifest lookup)
    SOURCE_TO_ENTRY = {v: k for k, v in ENTRY_TO_SOURCE.items()}
    
    # In dev mode, we need to use the request host and source paths
    if settings.DEBUG and hasattr(settings, 'DJANGO_VITE'):
        djv_config = settings.DJANGO_VITE.get('default', {})
        if djv_config.get('dev_mode', False):
            request = context.get('request')
            if request:
                vite_url = get_vite_dev_server_url(request)
                # Convert entry name to source path if needed
                source_path = ENTRY_TO_SOURCE.get(path, path)
                # Return the dev server URL for the asset
                # Vite serves assets from /static/ in dev mode
                return f'{vite_url}/static/{source_path}'
    
    # In production mode, try django-vite with manifest lookup
    # The manifest uses entry names as keys, so convert source paths to entry names if needed
    try:
        # First try with the path as-is (might be entry name or source path)
        return django_vite_asset_url(context, path)
    except Exception:
        # If that fails, try converting source path to entry name
        entry_name = SOURCE_TO_ENTRY.get(path, path)
        if entry_name != path:
            try:
                return django_vite_asset_url(context, entry_name)
            except Exception:
                pass
        # Final fallback - use source path directly
        source_path = ENTRY_TO_SOURCE.get(path, path)
        return f'/static/{source_path}'


@register.simple_tag(takes_context=True)
def vite_asset(context, path):
    """
    Custom vite_asset tag that handles path conversion from source paths to entry names.
    This wraps django-vite's vite_asset tag to work with both dev and production.
    """
    from django_vite.templatetags.django_vite import vite_asset as django_vite_asset
    
    # Mapping from entry names to source paths (for dev mode)
    ENTRY_TO_SOURCE = {
        'site-base-css': 'assets/styles/site-base.css',
        'site-tailwind-css': 'assets/styles/site-tailwind.css',
        'site': 'assets/javascript/site.js',
        'app': 'assets/javascript/app.js',
        'pegasus': 'assets/javascript/pegasus/pegasus.js',
        'react-object-lifecycle': 'assets/javascript/pegasus/examples/react/react-object-lifecycle.jsx',
        'vue-object-lifecycle': 'assets/javascript/pegasus/examples/vue/vue-object-lifecycle.js',
        'chat-ws-initialize': 'assets/javascript/chat/ws_initialize.ts',
    }
    
    # Reverse mapping from source paths to entry names (for production manifest lookup)
    SOURCE_TO_ENTRY = {v: k for k, v in ENTRY_TO_SOURCE.items()}
    
    # In dev mode, use source paths directly
    if settings.DEBUG and hasattr(settings, 'DJANGO_VITE'):
        djv_config = settings.DJANGO_VITE.get('default', {})
        if djv_config.get('dev_mode', False):
            # In dev mode, use source path as-is
            try:
                return django_vite_asset(context, path)
            except Exception:
                # Fallback
                source_path = ENTRY_TO_SOURCE.get(path, path)
                return f'<script type="module" src="/static/{source_path}"></script>'
    
    # In production mode, convert source paths to entry names for manifest lookup
    # The manifest uses entry names as keys, so prioritize conversion
    entry_name = SOURCE_TO_ENTRY.get(path, path)
    
    # Try with entry name first (production manifest uses entry names)
    if entry_name != path:
        try:
            return django_vite_asset(context, entry_name)
        except Exception:
            pass
    
    # If entry name conversion didn't work, try with original path (might already be entry name)
    try:
        return django_vite_asset(context, path)
    except Exception as e:
        # Log the error for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to load vite asset {path} (tried as entry name {entry_name}): {e}")
        # Final fallback - generate script tag with source path
        source_path = ENTRY_TO_SOURCE.get(path, path)
        return mark_safe(f'<script type="module" src="/static/{source_path}"></script>')

