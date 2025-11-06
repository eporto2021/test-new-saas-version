from django import forms
from django.utils.translation import gettext_lazy as _
from .models import UserDataFile


class DataFileUploadForm(forms.ModelForm):
    """
    Form for uploading data files for processing.
    """
    
    class Meta:
        model = UserDataFile
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={
                'class': 'block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 dark:text-gray-400 focus:outline-none dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400',
                'accept': '.csv,.json,.xlsx,.xls,.txt'
            })
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.service = kwargs.pop('service', None)
        super().__init__(*args, **kwargs)
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if not file:
            raise forms.ValidationError(_("Please select a file to upload."))
        
        # Check file size (10MB limit)
        if file.size > 10 * 1024 * 1024:
            raise forms.ValidationError(_("File size cannot exceed 10MB."))
        
        # Check file type
        allowed_extensions = ['.csv', '.json', '.xlsx', '.xls', '.txt']
        file_extension = '.' + file.name.split('.')[-1].lower()
        if file_extension not in allowed_extensions:
            raise forms.ValidationError(
                _("File type not supported. Allowed types: CSV, JSON, Excel, TXT")
            )
        
        return file
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.user = self.user
        if self.service:
            instance.service = self.service
        
        # Set original filename and file type
        instance.original_filename = self.cleaned_data['file'].name
        file_extension = '.' + self.cleaned_data['file'].name.split('.')[-1].lower()
        instance.file_type = file_extension[1:]  # Remove the dot
        
        if commit:
            instance.save()
        return instance
