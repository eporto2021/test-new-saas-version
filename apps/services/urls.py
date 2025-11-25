from django.urls import path

from . import views

app_name = 'services'

urlpatterns = [
    path('', views.services_home, name='services_home'),
    
    # Specific service URLs
    path('software-service-1/', views.software_service_1, name='software_service_1'),
    path('software-service-2/', views.software_service_2, name='software_service_2'),
    path('analytics/', views.analytics_dashboard, name='analytics_dashboard'),
    path('api/', views.api_access, name='api_access'),
    
    # Generic service URL for dynamic services
    path('<slug:service_slug>/', views.generic_service_view, name='generic_service'),
    
    # File upload and processing endpoints
    path('<slug:service_slug>/upload/', views.upload_data_file, name='upload_data_file'),
    path('<slug:service_slug>/process/', views.process_data_file, name='process_data_file'),
    path('<slug:service_slug>/delete/', views.delete_data_file, name='delete_data_file'),
    path('<slug:service_slug>/process-all/', views.process_all_files, name='process_all_files'),
    path('<slug:service_slug>/delete-all/', views.delete_all_files, name='delete_all_files'),
    path('<slug:service_slug>/delete-reports/', views.delete_processed_reports, name='delete_processed_reports'),
    path('file/<int:file_id>/status/', views.get_processing_status, name='get_processing_status'),
]
