from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
from django.urls import reverse
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json

from .models import Service, UserDataFile, UserProcessedData
from .decorators import service_access_required
from .helpers import get_user_accessible_services
from .forms import DataFileUploadForm


@login_required
def services_home(request):
    """
    Main services page showing all available services and user's access status.
    """
    accessible_services = get_user_accessible_services(request.user)
    all_services = Service.objects.filter(is_active=True).order_by('order', 'name')
    
    context = {
        'accessible_services': accessible_services,
        'all_services': all_services,
        'active_tab': 'services'
    }
    
    return render(request, 'services/services_home.html', context)


@service_access_required('software-service-1')
def software_service_1(request):
    """
    Example service 1 - replace with your actual service logic.
    """
    service = get_object_or_404(Service, slug='software-service-1')
    
    context = {
        'service': service,
        'active_tab': 'service-1'
    }
    
    return render(request, 'services/service_template.html', context)


@service_access_required('software-service-2')
def software_service_2(request):
    """
    Example service 2 - replace with your actual service logic.
    """
    service = get_object_or_404(Service, slug='software-service-2')
    
    context = {
        'service': service,
        'active_tab': 'service-2'
    }
    
    return render(request, 'services/service_template.html', context)


@service_access_required('analytics-dashboard')
def analytics_dashboard(request):
    """
    Example analytics service - replace with your actual analytics logic.
    """
    service = get_object_or_404(Service, slug='analytics-dashboard')
    
    context = {
        'service': service,
        'active_tab': 'analytics'
    }
    
    return render(request, 'services/service_template.html', context)


@service_access_required('api-access')
def api_access(request):
    """
    Example API access service - replace with your actual API logic.
    """
    service = get_object_or_404(Service, slug='api-access')
    
    context = {
        'service': service,
        'active_tab': 'api'
    }
    
    return render(request, 'services/service_template.html', context)


# Generic service view that can handle any service by slug
def generic_service_view(request, service_slug):
    """
    Generic view for any service - uses the service_access_required decorator dynamically.
    Handles file uploads and displays user data.
    """
    service = get_object_or_404(Service, slug=service_slug, is_active=True)
    
    # Check access manually since we can't use the decorator with dynamic slugs
    from .helpers import user_has_service_access
    
    if not user_has_service_access(request.user, service_slug):
        messages.error(
            request, 
            _("Sorry, you don't have access to {service_name}. Please upgrade your subscription to access this service.").format(
                service_name=service.name
            )
        )
        return render(request, 'services/no_access.html', {
            'service': service,
            'upgrade_url': reverse('subscriptions:subscription')
        }, status=403)
    
    # Handle file upload
    if request.method == 'POST':
        form = DataFileUploadForm(request.POST, request.FILES, user=request.user, service=service)
        if form.is_valid():
            data_file = form.save()
            messages.success(request, _("File uploaded successfully! Status: Pending."))
            
            return redirect('services:generic_service', service_slug=service_slug)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = DataFileUploadForm(user=request.user, service=service)
    
    # Get user's data files for this service
    user_data_files = UserDataFile.objects.filter(
        user=request.user, 
        service=service
    ).order_by('-created_at')[:10]  # Show last 10 files
    
    # Get processed data
    processed_data = UserProcessedData.objects.filter(
        data_file__user=request.user,
        data_file__service=service
    ).order_by('-created_at')[:5]  # Show last 5 processed files
    
    # Get user's custom template if it exists
    from django.conf import settings
    from pathlib import Path
    import logging
    
    logger = logging.getLogger(__name__)
    user_template_path = None
    
    # Priority 1: Check if user has a user-specific template
    user_specific_template = settings.USER_PROGRAMS_DIR / f"user_{request.user.id}" / service.name / "template.html"
    logger.info(f"Looking for user-specific template at: {user_specific_template}")
    
    if user_specific_template.exists():
        user_template_path = f"user_{request.user.id}/{service.name}/template.html"
        logger.info(f"Found user-specific template: {user_template_path}")
    else:
        # Priority 2: Check for service-level template (shared across all users)
        service_level_template = settings.USER_PROGRAMS_DIR / service.name / "template.html"
        logger.info(f"Looking for service-level template at: {service_level_template}")
        
        if service_level_template.exists():
            user_template_path = f"{service.name}/template.html"
            logger.info(f"Found service-level template: {user_template_path}")
        else:
            logger.info("No custom template found, will use default")
    
    context = {
        'service': service,
        'active_tab': f'service-{service_slug}',
        'form': form,
        'user_data_files': user_data_files,
        'processed_data': processed_data,
        'service_slug': service_slug,
        'user_template_path': user_template_path,
    }
    
    return render(request, 'services/service_with_data.html', context)


@login_required
@require_http_methods(["POST"])
def upload_data_file(request, service_slug):
    """
    AJAX endpoint for file uploads.
    """
    service = get_object_or_404(Service, slug=service_slug, is_active=True)
    
    # Check access
    from .helpers import user_has_service_access
    if not user_has_service_access(request.user, service_slug):
        return JsonResponse({
            'success': False,
            'error': 'Access denied'
        }, status=403)
    
    form = DataFileUploadForm(request.POST, request.FILES, user=request.user, service=service)
    
    if form.is_valid():
        data_file = form.save()
        
        return JsonResponse({
            'success': True,
            'file_id': data_file.id,
            'message': 'File uploaded successfully! Status: Pending.'
        })
    else:
        return JsonResponse({
            'success': False,
            'errors': form.errors
        }, status=400)


@login_required
def get_processing_status(request, file_id):
    """
    Get the processing status of a data file.
    """
    try:
        data_file = UserDataFile.objects.get(id=file_id, user=request.user)
        return JsonResponse({
            'status': data_file.processing_status,
            'log': data_file.processing_log,
            'processed_at': data_file.processed_at.isoformat() if data_file.processed_at else None
        })
    except UserDataFile.DoesNotExist:
        return JsonResponse({'error': 'File not found'}, status=404)


@login_required
@require_http_methods(["POST"])
def process_data_file(request, service_slug):
    """
    Process a specific data file.
    """
    try:
        data = json.loads(request.body)
        file_id = data.get('file_id')
        
        if not file_id:
            return JsonResponse({'success': False, 'error': 'File ID is required'}, status=400)
        
        # Get the file and verify ownership
        data_file = UserDataFile.objects.get(id=file_id, user=request.user)
        
        # Import the task here to avoid circular imports
        from .tasks import process_user_data_file
        
        # Start the processing task
        process_user_data_file.delay(file_id)
        
        return JsonResponse({'success': True, 'message': 'Processing started'})
        
    except UserDataFile.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'File not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def delete_data_file(request, service_slug):
    """
    Delete a specific data file.
    """
    try:
        data = json.loads(request.body)
        file_id = data.get('file_id')
        
        if not file_id:
            return JsonResponse({'success': False, 'error': 'File ID is required'}, status=400)
        
        # Get the file and verify ownership
        data_file = UserDataFile.objects.get(id=file_id, user=request.user)
        
        # Delete the file and its processed data
        data_file.delete()
        
        return JsonResponse({'success': True, 'message': 'File deleted successfully'})
        
    except UserDataFile.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'File not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def process_all_files(request, service_slug):
    """
    Process all uploaded files for a user (regardless of status).
    """
    try:
        # Import the batch task here to avoid circular imports
        from .tasks import process_all_user_files
        
        # Get service
        service = get_object_or_404(Service, slug=service_slug)

        # Kick off one batch job for this user+service
        process_all_user_files.delay(request.user.id, service_slug)

        # Respond with count for UX - count ALL files for this service
        file_count = UserDataFile.objects.filter(user=request.user, service=service).count()
        if file_count == 0:
            return JsonResponse({'success': False, 'error': 'No files to process. Please upload files first.'}, status=400)

        return JsonResponse({
            'success': True,
            'message': f'Processing started for {file_count} file(s)',
            'file_count': file_count
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def delete_all_files(request, service_slug):
    """
    Delete all files for a user.
    """
    try:
        # Scope to this service only
        service = get_object_or_404(Service, slug=service_slug, is_active=True)
        user_files = UserDataFile.objects.filter(user=request.user, service=service)
        
        if not user_files.exists():
            return JsonResponse({'success': False, 'error': 'No files to delete'}, status=400)
        
        file_count = user_files.count()

        # Delete associated processed data first (to ensure storage cleanup)
        processed_qs = UserProcessedData.objects.filter(data_file__in=user_files)
        for processed in processed_qs:
            # delete storage file
            if processed.processed_file:
                processed.processed_file.delete(save=False)
            processed.delete()
        
        # Delete uploaded files and their storage objects
        for df in user_files:
            if df.file:
                df.file.delete(save=False)
            df.delete()
        
        return JsonResponse({
            'success': True, 
            'message': f'Successfully deleted {file_count} file(s)',
            'deleted_count': file_count
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
