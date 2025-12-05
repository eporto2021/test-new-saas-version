"""
Middleware to configure django-vite dev server URL based on request host.
This allows the Vite dev server to work when accessing the app via network IP.
"""


class ViteDevServerMiddleware:
    """
    Middleware that dynamically sets the Vite dev server URL based on the request host.
    This ensures that when accessing the app via network IP, Vite assets load correctly.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only modify in development mode
        from django.conf import settings
        
        if settings.DEBUG and hasattr(settings, 'DJANGO_VITE'):
            # Get the request host (could be localhost or network IP)
            request_host = request.get_host().split(':')[0]  # Remove port if present
            
            # Update dev server URL to use request host
            # This ensures Vite assets load from the correct host
            if 'default' in settings.DJANGO_VITE:
                # Set dev server URL to use request host
                # django-vite will use this to generate asset URLs
                settings.DJANGO_VITE['default']['dev_server_url'] = f'http://{request_host}:5173'
        
        response = self.get_response(request)
        return response

