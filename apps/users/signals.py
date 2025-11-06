from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.files.storage import default_storage
from django.conf import settings
import os
import logging

from .models import CustomUser

logger = logging.getLogger(__name__)


@receiver(post_save, sender=CustomUser)
def create_user_template_folder(sender, instance, created, **kwargs):
    """
    Create user-specific template folder and default template when a new user is created.
    """
    if created:
        try:
            user_folder = f"user_templates/user_{instance.id}"
            
            # Create the user folder
            if not default_storage.exists(user_folder):
                # Create a dummy file to ensure the folder exists
                dummy_file_path = f"{user_folder}/.gitkeep"
                default_storage.save(dummy_file_path, content=b'')
                logger.info(f"Created user template folder: {user_folder}")
            
            # Create default template files for each active service
            create_default_user_templates(instance, user_folder)
            
        except Exception as e:
            logger.error(f"Failed to create user template folder for user {instance.id}: {str(e)}")


def create_default_user_templates(user, user_folder):
    """
    Create default template files for the user based on available services.
    """
    try:
        # Get the default template content
        default_template_path = "subscriptions/file_upload_service_example.html"
        
        # Read the default template content
        if default_storage.exists(default_template_path):
            with default_storage.open(default_template_path, 'r') as f:
                template_content = f.read()
        else:
            # Fallback template content
            template_content = """
{% load i18n %}

<div class="mt-6">
    <h2 class="pg-subtitle">{% translate "Upload & Process Data" %}</h2>
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border border-gray-200 dark:border-gray-700">
      <form method="post" enctype="multipart/form-data" action="{% url 'services:upload_data_file' service_slug=service_slug %}" onsubmit="return validateFileCount()">
        {% csrf_token %}
        <div class="mb-4">
          <label for="file-input" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            {% translate "Select data files (up to 10)" %}
          </label>
          <input type="file" name="file" id="file-input" 
                 accept=".csv,.json,.xlsx,.xls,.txt" 
                 multiple
                 onchange="checkFileLimit()"
                 class="block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 dark:text-gray-400 focus:outline-none dark:bg-gray-700 dark:border-gray-600"
                 required>
          <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
            {% translate "Supported formats: CSV, JSON, Excel (XLSX/XLS), TXT. Max size: 10MB per file. Up to 10 files allowed." %}
          </p>
          <p id="file-error" class="mt-1 text-sm text-red-600 dark:text-red-400 hidden">
            {% translate "You can only upload up to 10 files." %}
          </p>
        </div>
        
        <button type="submit" class="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
          <i class="fa fa-upload mr-2"></i>
          {% translate "Upload & Process" %}
        </button>
      </form>
    </div>
  </div>

  <!-- JavaScript for file limit validation -->
  <script>
    function checkFileLimit() {
      const fileInput = document.getElementById('file-input');
      const errorMessage = document.getElementById('file-error');
      if (fileInput.files.length > 10) {
        errorMessage.classList.remove('hidden');
        fileInput.value = '';
        return false;
      } else {
        errorMessage.classList.add('hidden');
        return true;
      }
    }

    function validateFileCount() {
      return checkFileLimit();
    }
  </script>

  <!-- Recent Uploads & Processed Data -->
  {% if user_data_files or processed_data %}
  <div class="mt-6">
    <h2 class="pg-subtitle">{% translate "Your Files" %}</h2>
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">

      <!-- Recent Uploads -->
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border border-gray-200 dark:border-gray-700">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          <i class="fa fa-file mr-2"></i>
          {% translate "Recent Uploads" %}
        </h3>
        
        {% if user_data_files %}
          <div class="space-y-3">
            {% for file in user_data_files %}
              <div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div class="flex-1">
                  <div class="flex items-center">
                    <i class="fa fa-file-{% if file.file_type == 'csv' %}csv{% elif file.file_type == 'json' %}code{% elif file.file_type in 'xlsx,xls' %}excel{% else %}text{% endif %} mr-2 text-gray-500"></i>
                    <span class="font-medium text-gray-900 dark:text-white">{{ file.original_filename }}</span>
                  </div>
                  <div class="text-sm text-gray-500 dark:text-gray-400 mt-1">
                    {{ file.file_size_human }} • {{ file.created_at|date:"M d, Y H:i" }}
                  </div>
                </div>
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium
                    {% if file.processing_status == 'completed' %}bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300
                    {% elif file.processing_status == 'processing' %}bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300
                    {% elif file.processing_status == 'failed' %}bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300
                    {% else %}bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300{% endif %}">
                  {{ file.get_processing_status_display }}
                </span>
              </div>
            {% endfor %}
          </div>
        {% else %}
          <p class="text-gray-500 dark:text-gray-400">{% translate "No files uploaded yet." %}</p>
        {% endif %}
      </div>

      <!-- Processed Data -->
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border border-gray-200 dark:border-gray-700">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          <i class="fa fa-download mr-2"></i>
          {% translate "Processed Files" %}
        </h3>
        
        {% if processed_data %}
          <div class="space-y-3">
            {% for data in processed_data %}
              <div class="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div class="flex items-center justify-between mb-2">
                  <span class="font-medium text-gray-900 dark:text-white">
                    {{ data.data_file.original_filename }}
                  </span>
                  <span class="text-sm text-gray-500 dark:text-gray-400">
                    {{ data.created_at|date:"M d, Y" }}
                  </span>
                </div>
                
                {% if data.summary_data %}
                  <div class="text-sm text-gray-600 dark:text-gray-300 mb-2">
                    <span class="font-medium">Rows:</span> {{ data.summary_data.processed_rows|default:"N/A" }}
                  </div>
                {% endif %}
                
                <a href="{{ data.processed_file.url }}" 
                   class="inline-flex items-center text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400" download>
                  <i class="fa fa-download mr-1"></i>
                  {% translate "Download" %}
                </a>
              </div>
            {% endfor %}
          </div>
        {% else %}
          <p class="text-gray-500 dark:text-gray-400">{% translate "No processed files yet." %}</p>
        {% endif %}
      </div>
    </div>
  </div>
  {% endif %}
"""
        
        # Create template files for common service slugs
        common_service_slugs = ['data-cleansing', 'email-marketing', 'bulk-text', 'payroll', 'stock-take']
        
        for service_slug in common_service_slugs:
            template_filename = f"file_upload_service_{service_slug}.html"
            template_path = f"{user_folder}/{template_filename}"
            
            # Only create if it doesn't exist
            if not default_storage.exists(template_path):
                default_storage.save(template_path, content=template_content.encode('utf-8'))
                logger.info(f"Created default template: {template_path}")
        
        logger.info(f"Successfully created default templates for user {user.id}")
        
    except Exception as e:
        logger.error(f"Failed to create default templates for user {user.id}: {str(e)}")