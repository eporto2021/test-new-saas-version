# flake8: noqa: F405
from .settings import *  # noqa F401

# Note: it is recommended to use the "DEBUG" environment variable to override this value in your main settings.py file.
# A future release may remove it from here.
DEBUG = False

# fix ssl mixed content issues
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Django security checklist settings.
# More details here: https://docs.djangoproject.com/en/stable/howto/deployment/checklist/
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# HTTP Strict Transport Security settings
# Without uncommenting the lines below, you will get security warnings when running ./manage.py check --deploy
# https://docs.djangoproject.com/en/stable/ref/middleware/#http-strict-transport-security

# # Increase this number once you're confident everything works https://stackoverflow.com/a/49168623/8207
# SECURE_HSTS_SECONDS = 60
# # Uncomment these two lines if you are sure that you don't host any subdomains over HTTP.
# # You will get security warnings if you don't do this.
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True

USE_HTTPS_IN_ABSOLUTE_URLS = True

# If you don't want to use environment variables to set production hosts you can add them here
ALLOWED_HOSTS = ["test-blue-smoke-97.fly.dev",'localhost']

# Your email config goes here.
# see https://github.com/anymail/django-anymail for more details / examples
# To use MailerSend, make sure your API key is available in the environment.

# Only use MailerSend if API key is provided and not empty, otherwise fall back to console
mailersend_api_key = env("MAILERSEND_API_KEY", default=None)
if mailersend_api_key and mailersend_api_key.strip():
    try:
        print("MailerSend API key is set, configuring email backend")
        EMAIL_BACKEND = "anymail.backends.mailersend.EmailBackend"
        ANYMAIL = {
            "MAILERSEND_API_TOKEN": mailersend_api_key,
            "MAILERSEND_API_URL": env("MAILERSEND_API_URL", default="https://api.mailersend.com/v1"),
        }
        import logging
        logger = logging.getLogger(__name__)
        logger.info("MailerSend email backend configured")
    except Exception as e:
        # Fallback to console if MailerSend configuration fails
        EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"MailerSend configuration failed: {e}, falling back to console email backend")
else:
    # Fallback to console backend if MailerSend is not configured
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
    import logging
    logger = logging.getLogger(__name__)
    logger.warning("MAILERSEND_API_KEY not set or empty, using console email backend")

ADMINS = [
    ("Your Name", "maxdavenport96@gmail.com"),
]

# Production Stripe settings
STRIPE_LIVE_MODE = True

# Production-specific product configuration
# These override the ACTIVE_PRODUCTS and ACTIVE_ECOMMERCE_PRODUCT_IDS from settings.py
# Use LIVE Stripe product IDs here (not test mode product IDs)

# Subscription products (recurring billing) - LIVE product IDs
ACTIVE_PRODUCTS = [
    'prod_TMOpLmL5vnKtCX', # Optimo Route Formatter
    'prod_TMOxLctPXHGeUr', # Bulk payment link creator
    'prod_T3ys3097fCjBPl',# Check Each Drop off Has A Pick Up
    'prod_TH8G6pq4cSCVBc', # Role Based Staff Training Website
    'prod_SoHjyWHk63DnzD', # Check each booking is on the run sheet as a drop off
    'prod_TMPLzH7z6lE74v', # Estimated Time of Arrival bulk SMS program
]

# Ecommerce products (one-time purchases) - LIVE product IDs
ACTIVE_ECOMMERCE_PRODUCT_IDS = [
    # Add your LIVE one-time purchase product IDs here
    # Example: 'prod_LIVE_ECOMMERCE_ID',
]

# Media files (uploads) storage
# Use /data volume mounted by Fly.io for persistent storage
import os

# Override MEDIA_ROOT to use persistent volume (must be string, not Path)
MEDIA_ROOT = '/data/media'
# Keep MEDIA_URL consistent with base settings
MEDIA_URL = '/media/'
# Ensure the media directory exists
os.makedirs(MEDIA_ROOT, exist_ok=True)
