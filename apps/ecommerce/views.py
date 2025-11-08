import os

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models
from django.http import FileResponse, Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import gettext as _

from apps.ecommerce.decorators import product_required
from apps.subscriptions.metadata import get_active_products_with_metadata
from apps.utils.billing import get_stripe_module
from apps.web.meta import absolute_url

from .helpers import create_purchase_from_checkout_session
from .models import ProductConfiguration, Purchase


@login_required
def ecommerce_home(request):
    products = (
        ProductConfiguration.objects.filter(is_active=True)
        .select_related("product", "product__default_price")
        .order_by("-created_at")
    ).annotate(
        owned=models.Subquery(
            models.Exists(
                Purchase.objects.filter(product_configuration=models.OuterRef("pk"), is_valid=True, user=request.user)
            )
        )
    )

    # Always get subscription products for display
    subscription_products = list(get_active_products_with_metadata())
    
    # Get demo links for subscription products from ProductDemoLink
    from apps.subscriptions.models import ProductDemoLink, SubscriptionRequest
    demo_links = {}
    for product in subscription_products:
        try:
            demo_link = ProductDemoLink.objects.get(
                stripe_product_id=product.product.id,
                is_active=True
            )
            demo_links[product.product.id] = demo_link
        except ProductDemoLink.DoesNotExist:
            pass
    
    # Get approved demo requests for the current user (to use demo_url from request)
    approved_demo_urls = {}
    if request.user.is_authenticated:
        approved_demos = SubscriptionRequest.objects.filter(
            user=request.user,
            request_type='demo',
            status='approved'
        ).exclude(demo_url='')
        for demo in approved_demos:
            approved_demo_urls[demo.product_stripe_id] = demo.demo_url

    return TemplateResponse(
        request,
        "ecommerce/ecommerce_home.html",
        {
            "active_tab": "ecommerce",
            "products": products,
            "subscription_products": subscription_products,
            "demo_links": demo_links,
            "approved_demo_urls": approved_demo_urls,
        },
    )


@login_required
def purchase_product(request, product_slug: str):
    product_config = get_object_or_404(
        ProductConfiguration.objects.select_related("product", "product__default_price"), slug=product_slug
    )
    stripe = get_stripe_module()
    success_url = absolute_url(reverse("ecommerce:checkout_success", args=[product_slug]))
    cancel_url = absolute_url(reverse("ecommerce:checkout_cancelled", args=[product_slug]))
    customer_kwargs = {}
    if request.user.customer:
        customer_kwargs["customer"] = request.user.customer.id
    else:
        customer_kwargs["customer_email"] = request.user.email
        # create a customer object so we can re-use it in future payments
        customer_kwargs["customer_creation"] = "always"

    checkout_session = stripe.checkout.Session.create(
        success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}",
        cancel_url=cancel_url,
        payment_method_types=["card"],
        client_reference_id=request.user.id,
        mode="payment" if not product_config.product.default_price.recurring else "subscription",
        line_items=[
            {
                "price": product_config.product.default_price.id,
                "quantity": 1,
            },
        ],
        allow_promotion_codes=True,
        metadata={
            "source": "ecommerce",  # used by the webhook to only process checkouts from here
            "product_configuration_id": product_config.id,
        },
        **customer_kwargs,
    )
    return HttpResponseRedirect(checkout_session.url)


@login_required
def checkout_success(request, product_slug: str):
    # handle fulfillment
    product_config = get_object_or_404(ProductConfiguration.objects.select_related("product"), slug=product_slug)
    session_id = request.GET.get("session_id")
    if not session_id:
        messages.error(
            request,
            "Couldn't find a Stripe session for your payment. If you think this is an error, please get in touch.",
        )
        return TemplateResponse(request, "400.html", status=400)

    session = get_stripe_module().checkout.Session.retrieve(session_id, expand=["line_items"])
    if session.payment_status != "paid":
        messages.error(
            request,
            "Sorry, it looks like your payment didn't go through. If you think this is an error, please get in touch.",
        )
        return TemplateResponse(request, "400.html", status=400)

    client_reference_id = int(session.client_reference_id)
    if client_reference_id != request.user.id:
        raise ValueError("User ID from checkout session did not match the logged-in user!")
    product_configuration_id = int(session.metadata.get("product_configuration_id"))
    if product_configuration_id != product_config.id:
        raise ValueError("Product configuration ID from checkout session did not match the product configuration!")
    create_purchase_from_checkout_session(session, product_config)
    messages.success(
        request,
        _("Your purchase of {product_name} was successful. Thanks for the support!").format(
            product_name=product_config.product.name
        ),
    )
    return HttpResponseRedirect(reverse("ecommerce:access_product", args=[product_slug]))


@login_required
def checkout_cancelled(request, product_slug: str):
    product_config = get_object_or_404(ProductConfiguration.objects.select_related("product"), slug=product_slug)
    messages.info(
        request, _("Your purchase of {product_name} was cancelled.").format(product_name=product_config.product.name)
    )
    return HttpResponseRedirect(reverse("ecommerce:ecommerce_home"))


@login_required
def purchases(request):
    purchases = Purchase.objects.filter(user=request.user)
    return TemplateResponse(
        request,
        "ecommerce/purchases.html",
        {
            "active_tab": "ecommerce",
            "purchases": purchases,
        },
    )


@login_required
@product_required
def access_product(request, product_slug: str):
    return TemplateResponse(
        request,
        "ecommerce/access_product.html",
        {
            "active_tab": "ecommerce",
            "product_config": request.product_config,  # set by the decorator
            "purchase": request.product_purchase,  # set by the decorator
        },
    )


@login_required
@product_required
def download_product_file(request, product_slug: str):
    """
    Download view for files attached to products.
    Only accessible to users who have purchased the product.
    """
    product_config = request.product_config  # set by the decorator

    if not product_config.content:
        raise Http404(_("No attachment is available for this product."))

    # Get the original filename for the download
    filename = os.path.basename(product_config.content.name)

    try:
        # Open the file using the storage backend.
        # FileResponse will handle closing the file object.
        file_object = product_config.content.open("rb")
    except FileNotFoundError:
        raise Http404(_("The digital file could not be found or accessed on the storage backend.")) from None

    return FileResponse(file_object, as_attachment=True, filename=filename)
