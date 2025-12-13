from functools import wraps
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from django.urls import reverse

from .models import UserServiceAccess, Service


def service_access_required(service_slug):
    """
    Decorator that checks if a user has access to a specific service.
    
    Usage:
        @service_access_required('software-service-1')
        def my_service_view(request):
            # User has access to this service
            pass
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, _("You must be logged in to access this service."))
                return HttpResponseForbidden(render(request, '403.html', status=403))
            
            try:
                service = Service.objects.get(slug=service_slug, is_active=True)
            except Service.DoesNotExist:
                messages.error(request, _("This service is not available."))
                return HttpResponseForbidden(render(request, '403.html', status=403))
            
            # Check if user has active access to this service
            has_access = UserServiceAccess.objects.filter(
                user=request.user,
                service=service,
                is_active=True
            ).exists()
            
            # Also check if access hasn't expired
            if has_access:
                access = UserServiceAccess.objects.get(user=request.user, service=service)
                if not access.is_valid:
                    has_access = False
            
            if not has_access:
                error_msg = _(
                    "Sorry, you don't have access to {service_name}. "
                    "Please upgrade your subscription to access this service."
                ).format(service_name=service.name)
                messages.error(request, error_msg)
                return render(request, 'services/no_access.html', {
                    'service': service,
                    'upgrade_url': reverse('subscriptions:subscription')
                }, status=403)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def service_access_required_ajax(service_slug):
    """
    AJAX version of the service access decorator that returns JSON error responses.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return JsonResponse({
                    'error': _("You must be logged in to access this service.")
                }, status=401)
            
            try:
                service = Service.objects.get(slug=service_slug, is_active=True)
            except Service.DoesNotExist:
                return JsonResponse({
                    'error': _("This service is not available.")
                }, status=404)
            
            # Check if user has active access to this service
            has_access = UserServiceAccess.objects.filter(
                user=request.user,
                service=service,
                is_active=True
            ).exists()
            
            if has_access:
                access = UserServiceAccess.objects.get(user=request.user, service=service)
                if not access.is_valid:
                    has_access = False
            
            if not has_access:
                error_msg = _(
                    "Sorry, you don't have access to {service_name}. "
                    "Please upgrade your subscription."
                ).format(service_name=service.name)
                return JsonResponse({
                    'error': error_msg,
                    'upgrade_url': reverse('subscriptions:subscription')
                }, status=403)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
