import logging

import requests
from allauth.account.forms import SignupForm
from django import forms
from django.conf import settings
from django.contrib.auth.forms import UserChangeForm
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from apps.utils.timezones import get_timezones_display

from .helpers import validate_profile_picture
from .models import CustomUser


class TurnstileSignupForm(SignupForm):
    """
    Sign up form that includes a turnstile captcha.
    """

    turnstile_token = forms.CharField(widget=forms.HiddenInput(), required=False)

    def clean_turnstile_token(self):
        if not settings.TURNSTILE_SECRET:
            logging.info("No turnstile secret found, not checking captcha")
            return

        turnstile_token = self.cleaned_data.get("turnstile_token", None)
        if not turnstile_token:
            raise forms.ValidationError("Missing captcha. Please try again.")

        turnstile_url = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
        payload = {
            "secret": settings.TURNSTILE_SECRET,
            "response": turnstile_token,
        }
        try:
            response = requests.post(turnstile_url, data=payload, timeout=10).json()
            if not response["success"]:
                raise forms.ValidationError("Invalid captcha. Please try again.")
        except requests.Timeout:
            raise forms.ValidationError("Captcha verification timed out. Please try again.") from None

        return turnstile_token


class CustomUserChangeForm(UserChangeForm):
    email = forms.EmailField(label=_("Email"), required=True)
    language = forms.ChoiceField(label=_("Language"))
    timezone = forms.ChoiceField(label=_("Time Zone"), required=False)

    class Meta:
        model = CustomUser
        fields = ("email", "first_name", "last_name", "language", "timezone")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        timezone = self.fields.get("timezone")
        timezone.choices = get_timezones_display()
        if settings.USE_I18N and len(settings.LANGUAGES) > 1:
            language = self.fields.get("language")
            language.choices = settings.LANGUAGES
        else:
            self.fields.pop("language")


class UploadAvatarForm(forms.Form):
    avatar = forms.FileField(validators=[validate_profile_picture])


class TermsSignupForm(TurnstileSignupForm):
    """Custom signup form to add a checkbox for accepting the terms."""

    first_name = forms.CharField(
        label=_("First Name"),
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': _('First Name'),
            'class': 'pg-input'
        })
    )
    terms_agreement = forms.BooleanField(required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add CSS classes to form fields to prevent template errors
        self.fields['email'].widget.attrs.update({'class': 'pg-input'})
        self.fields['password1'].widget.attrs.update({'class': 'pg-input'})
        self.fields['terms_agreement'].widget.attrs.update({'class': 'checkbox'})
        # Add class to honeypot field to prevent template errors
        if 'phone_number_x' in self.fields:
            self.fields['phone_number_x'].widget.attrs.update({'class': 'hidden'})
        # Add class to turnstile token field
        if 'turnstile_token' in self.fields:
            self.fields['turnstile_token'].widget.attrs.update({'class': 'hidden'})
        # blank out overly-verbose help text
        self.fields["password1"].help_text = ""
        link = '<a class="link" href="{}" target="_blank">{}</a>'.format(
            reverse("web:terms"),
            _("Terms and Conditions"),
        )
        self.fields["terms_agreement"].label = mark_safe(_("I agree to the {terms_link}").format(terms_link=link))
    
    def save(self, request):
        user = super().save(request)
        user.first_name = self.cleaned_data.get('first_name', '')
        user.save()
        return user
