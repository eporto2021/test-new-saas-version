import logging
import os
from django.core.files.storage import default_storage

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import mail_admins
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods
from djstripe.enums import SubscriptionStatus
from djstripe.models import Product
from stripe.error import InvalidRequestError

from apps.utils.billing import get_stripe_module

from ..decorators import active_subscription_required, redirect_subscription_errors
from ..forms import UsageRecordForm
from ..helpers import get_subscription_urls, subscription_is_active, subscription_is_trialing
from ..metadata import ACTIVE_PLAN_INTERVALS, get_active_plan_interval_metadata, get_active_products_with_metadata
from ..models import SubscriptionModelBase, SubscriptionRequest
from ..wrappers import InvoiceFacade, SubscriptionWrapper

log = logging.getLogger("test.subscription")


@redirect_subscription_errors
@login_required
def subscription(request):
    subscription_holder = request.user
    if subscription_holder.has_active_subscription():
        return _view_subscription(request, subscription_holder)
    else:
        # Show a simple message instead of the pricing table
        return render(
            request,
            "subscriptions/no_subscription.html",
            {
                "active_tab": "subscription",
                "page_title": _("Subscription"),
            },
        )


def _view_subscription(request, subscription_holder: SubscriptionModelBase):
    """
    Show user's active subscriptions
    """
    assert subscription_holder.has_active_subscription()
    
    # Get all active subscriptions for the user's customer
    from djstripe.models import Subscription
    from djstripe.enums import SubscriptionStatus
    
    all_subscriptions = []
    if subscription_holder.customer:
        # Get all active subscriptions for this customer
        customer_subscriptions = Subscription.objects.filter(
            customer=subscription_holder.customer,
            status__in=[SubscriptionStatus.active, SubscriptionStatus.trialing, SubscriptionStatus.past_due]
        ).order_by('-created')
        
        all_subscriptions = [SubscriptionWrapper(sub) for sub in customer_subscriptions]
    
    # For backward compatibility, also get the primary subscription
    primary_subscription = subscription_holder.active_stripe_subscription
    next_invoice = None
    
    if primary_subscription:
        if subscription_is_trialing(primary_subscription) and not primary_subscription.default_payment_method:
            # trialing subscriptions with no payment method set don't have invoices so we can skip that check
            pass
        elif not primary_subscription.cancel_at_period_end:
            stripe = get_stripe_module()
            try:
                next_invoice = stripe.Invoice.create_preview(
                    subscription=primary_subscription.id,
                )
            except InvalidRequestError:
                # this error is raised if you try to get an invoice but the subscription is canceled or deleted
                # check if this happened and redirect to the upgrade page if so
                subscription_is_invalid = False
                try:
                    stripe_subscription = stripe.Subscription.retrieve(primary_subscription.id)
                except InvalidRequestError:
                    log.error(
                        "The subscription could not be retrieved from Stripe. "
                        "If you are running in test mode, it may have been deleted."
                    )
                    stripe_subscription = None
                    subscription_holder.subscription = None
                    subscription_holder.save()
                    subscription_is_invalid = True
                if stripe_subscription and (
                    stripe_subscription.status != SubscriptionStatus.active or stripe_subscription.cancel_at_period_end
                ):
                    log.warning(
                        "A canceled subscription was not synced to your app DB. "
                        "Your webhooks may not be set up properly. "
                        "See: https://docs.saaspegasus.com/subscriptions.html#webhooks"
                    )
                    # update the subscription in the database and clear from the subscription_holder
                    primary_subscription.sync_from_stripe_data(stripe_subscription)
                    subscription_is_invalid = True
                elif stripe_subscription:
                    # failed for some other unexpected reason.
                    raise

                if subscription_is_invalid:
                    subscription_holder.refresh_from_db()
                    subscription_holder.clear_cached_subscription()

                    if not subscription_is_active(primary_subscription):
                        return _upgrade_subscription(request, subscription_holder)

    wrapped_subscription = SubscriptionWrapper(primary_subscription) if primary_subscription else None
    
    return render(
        request,
        "subscriptions/view_subscription.html",
        {
            "active_tab": "subscription",
            "page_title": _("Subscriptions"),
            "subscription": wrapped_subscription,
            "all_subscriptions": all_subscriptions,
            "next_invoice": InvoiceFacade(next_invoice) if next_invoice else None,
            "subscription_urls": get_subscription_urls(subscription_holder),
        },
    )


def _upgrade_subscription(request, subscription_holder):
    """
    Show subscription upgrade form / options.
    """
    assert not subscription_holder.has_active_subscription()

    active_products = list(get_active_products_with_metadata())
    default_products = [p for p in active_products if p.metadata.is_default]
    default_product = default_products[0] if default_products else active_products[0]

    return render(
        request,
        "subscriptions/upgrade_subscription.html",
        {
            "active_tab": "subscription",
            "default_product": default_product,
            "active_products": active_products,
            "active_plan_intervals": get_active_plan_interval_metadata(),
            "default_interval": ACTIVE_PLAN_INTERVALS[0],
            "subscription_urls": get_subscription_urls(subscription_holder),
        },
    )


@login_required
def subscription_demo(request):
    subscription_holder = request.user
    subscription = subscription_holder.active_stripe_subscription
    wrapped_subscription = SubscriptionWrapper(subscription) if subscription else None
    return render(
        request,
        "subscriptions/demo.html",
        {
            "active_tab": "subscription_demo",
            "subscription": wrapped_subscription,
            "subscription_urls": get_subscription_urls(subscription_holder),
            "page_title": _("Subscription Demo"),
        },
    )


@login_required
@active_subscription_required
def subscription_gated_page(request):
    return render(request, "subscriptions/subscription_gated_page.html")


@login_required
@active_subscription_required
def metered_billing_demo(request):
    subscription_holder = request.user
    if request.method == "POST":
        form = UsageRecordForm(subscription_holder, request.POST)
        if form.is_valid():
            usage_data = form.save()
            messages.info(request, _("Successfully recorded {} units for metered billing.").format(usage_data.quantity))
            return HttpResponseRedirect(reverse("subscriptions:subscription_demo"))
    else:
        form = UsageRecordForm(subscription_holder)

    if not form.is_usable():
        messages.info(
            request,
            _(
                "It looks like you don't have any metered subscriptions set up. "
                "Sign up for a subscription with metered usage to use this UI."
            ),
        )
    return render(
        request,
        "subscriptions/metered_billing_demo.html",
        {
            "subscription": subscription_holder.active_stripe_subscription,
            "form": form,
        },
    )


@login_required
def subscription_service(request, service_slug):
    """
    View for individual subscription service pages.
    Shows details and functionality for a specific subscription service.
    """
    from django.shortcuts import get_object_or_404
    from djstripe.models import Subscription
    from djstripe.enums import SubscriptionStatus
    from django.utils.text import slugify
    from apps.services.helpers import get_or_create_service_from_product, grant_service_access
    
    # Get user's active subscriptions
    if not request.user.customer:
        messages.error(request, _("You don't have any active subscriptions."))
        return HttpResponseRedirect(reverse("subscriptions:subscription_details"))
    
    subscriptions = Subscription.objects.filter(
        customer=request.user.customer,
        status__in=[SubscriptionStatus.active, SubscriptionStatus.trialing, SubscriptionStatus.past_due]
    )
    
    # Find the subscription that matches the service slug
    matching_subscription = None
    for subscription in subscriptions:
        if subscription.items.exists():
            first_item = subscription.items.first()
            product = first_item.price.product
            if slugify(product.name) == service_slug:
                matching_subscription = subscription
                break
    
    if not matching_subscription:
        messages.error(request, _("You don't have access to this service."))
        return HttpResponseRedirect(reverse("subscriptions:subscription_details"))
    
    # Get the product details
    first_item = matching_subscription.items.first()
    product = first_item.price.product
    
    # Ensure the service exists in the services app and grant access
    service = get_or_create_service_from_product(product)
    grant_service_access(request.user, service.slug, matching_subscription)
    
    # Get user's data files and processed data for this service
    from apps.services.models import UserDataFile, UserProcessedData
    user_data_files = UserDataFile.objects.filter(
        user=request.user, 
        service=service
    ).order_by('-created_at')[:10]
    
    processed_data = UserProcessedData.objects.filter(
        data_file__user=request.user,
        data_file__service=service
    ).order_by('-created_at')[:5]
    
    # Get user-specific template path and cloud function URL
    user_template_path = get_user_template_path(request.user, product.name)
    cloud_function_url = get_user_cloud_function_url(request.user, product.name)
    upload_directory = get_user_upload_directory(request.user, product.name)
    processed_directory = get_user_processed_directory(request.user, product.name)
    
    context = {
        'subscription': SubscriptionWrapper(matching_subscription),
        'product': product,
        'service_slug': service.slug,  # Use the actual service slug
        'active_tab': f'subscription-{service_slug}',
        'page_title': product.name,
        'user_data_files': user_data_files,
        'processed_data': processed_data,
        'user_template_path': user_template_path,
        'cloud_function_url': cloud_function_url,
        'upload_directory': upload_directory,
        'processed_directory': processed_directory,
    }
    
    return render(request, "subscriptions/subscription_service.html", context)


def get_user_template_path(user, product_name):
    """
    Get the path to the user-specific template file.
    Returns the path to the user's custom template or a default fallback.
    """
    from pathlib import Path
    from django.conf import settings
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Use absolute path from USER_PROGRAMS_DIR to check if file exists
    # USER_PROGRAMS_DIR automatically uses development_programs or production_programs based on environment
    user_template_path = settings.USER_PROGRAMS_DIR / f"user_{user.id}" / product_name / "template.html"
    
    logger.info(f"Looking for user template at: {user_template_path}")
    logger.info(f"User ID: {user.id}, Product name: '{product_name}'")
    logger.info(f"Template exists: {user_template_path.exists()}")
    
    # Check if the user-specific template exists
    if user_template_path.exists():
        # Return path RELATIVE to USER_PROGRAMS_DIR (which is in TEMPLATES['DIRS'])
        template_path = f"user_{user.id}/{product_name}/template.html"
        logger.info(f"Returning template path: {template_path}")
        return template_path
    
    # Fallback to default template if user-specific doesn't exist
    logger.info("Falling back to default template")
    return "subscriptions/file_upload_service_example.html"


def get_user_cloud_function_url(user, product_name):
    """
    Get the user's custom cloud function URL for this product.
    Returns None if not configured.
    """
    from pathlib import Path
    from django.conf import settings
    
    # Use absolute path from USER_PROGRAMS_DIR (automatically uses dev or prod based on environment)
    cf_url_path = settings.USER_PROGRAMS_DIR / f"user_{user.id}" / product_name / "cloud_function_url.txt"
    
    try:
        if cf_url_path.exists():
            with open(cf_url_path, 'r') as f:
                return f.read().strip()
    except Exception:
        pass
    
    return None


def get_user_upload_directory(user, product_name):
    """
    Get the directory path where user's uploads should be stored.
    Uses environment-specific user programs directory (development_programs or production_programs).
    """
    from django.conf import settings
    env_folder = "production_programs" if settings.STRIPE_LIVE_MODE else "development_programs"
    return f"user_programs/{env_folder}/user_{user.id}/{product_name}/uploads/"


def get_user_processed_directory(user, product_name):
    """
    Get the directory path where user's processed files should be stored.
    Uses environment-specific user programs directory (development_programs or production_programs).
    """
    from django.conf import settings
    env_folder = "production_programs" if settings.STRIPE_LIVE_MODE else "development_programs"
    return f"user_programs/{env_folder}/user_{user.id}/{product_name}/processed/"


@login_required
@require_http_methods(["POST"])
def request_subscription(request, product_id):
    """
    Handle subscription request from user.
    Creates a request record and emails admins.
    """
    try:
        product = get_object_or_404(Product, id=product_id)
        
        # Create subscription request
        subscription_request = SubscriptionRequest.objects.create(
            user=request.user,
            product_name=product.name,
            product_stripe_id=product.id,
            message=request.POST.get('message', ''),
            status='pending'
        )
        
        # Send email to admins
        subject = f"New Subscription Request: {product.name}"
        message = f"""
User: {request.user.email}
Name: {request.user.get_full_name()}
Product: {product.name}
Product ID: {product.id}
Request Date: {subscription_request.created_at.strftime('%Y-%m-%d %H:%M:%S')}

Message from user:
{subscription_request.message or 'No message provided'}

View in admin: {request.build_absolute_uri(reverse('admin:subscriptions_subscriptionrequest_change', args=[subscription_request.id]))}
        """
        
        mail_admins(
            subject=subject,
            message=message,
            fail_silently=True,
        )
        
        messages.success(
            request,
            _("Your subscription request has been submitted! We'll contact you shortly to set up your trial.")
        )
        
        return HttpResponseRedirect(reverse('ecommerce:ecommerce_home'))
        
    except Exception as e:
        log.error(f"Error creating subscription request: {str(e)}")
        messages.error(
            request,
            _("There was an error submitting your request. Please try again or contact support.")
        )
        return HttpResponseRedirect(reverse('ecommerce:ecommerce_home'))
