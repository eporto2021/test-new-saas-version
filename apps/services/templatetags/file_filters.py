"""
Template filters for file-related operations.
"""

import os
from django import template

register = template.Library()


@register.filter
def filename(file_path):
    """
    Extract filename from a file path.
    
    Usage: {{ file_path|filename }}
    """
    if not file_path:
        return ""
    return os.path.basename(str(file_path))


@register.filter
def file_extension(file_path):
    """
    Extract file extension from a file path.
    
    Usage: {{ file_path|file_extension }}
    """
    if not file_path:
        return ""
    return os.path.splitext(str(file_path))[1].lower()


@register.filter
def file_size_human(bytes_value):
    """
    Convert bytes to human readable format.
    
    Usage: {{ file.size|file_size_human }}
    """
    if not bytes_value:
        return "0 B"
    
    try:
        bytes_value = int(bytes_value)
    except (ValueError, TypeError):
        return "0 B"
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    
    return f"{bytes_value:.1f} PB"
