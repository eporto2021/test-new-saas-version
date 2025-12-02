import rest_framework.serializers
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from apps.api.permissions import IsAuthenticatedOrHasUserAPIKey
from apps.users.models import CustomUser
from apps.services.models import Service, UserServiceAccess
from apps.services.helpers import user_has_service_access
from djstripe.models import Subscription
from djstripe.enums import SubscriptionStatus

from ..exceptions import SubscriptionConfigError
from ..helpers import create_stripe_checkout_session, create_stripe_portal_session
from ..metadata import ProductWithMetadata, get_active_products_with_metadata


@extend_schema(tags=["subscriptions"], exclude=True)
class ProductWithMetadataAPI(APIView):
    permission_classes = (IsAuthenticatedOrHasUserAPIKey,)

    @extend_schema(operation_id="active_products_list", responses={200: ProductWithMetadata.serializer()})
    def get(self, request, *args, **kw):
        products_with_metadata = get_active_products_with_metadata()
        return Response(data=[p.to_dict() for p in products_with_metadata])


@extend_schema(tags=["subscriptions"], exclude=True)
class CreateCheckoutSession(APIView):
    @extend_schema(
        operation_id="create_checkout_session",
        request=inline_serializer("CreateCheckout", {"priceid": rest_framework.serializers.CharField()}),
        responses={
            200: OpenApiTypes.URI,
        },
    )
    def post(self, request):
        subscription_holder = request.user
        price_id = request.POST["priceId"]
        checkout_session = create_stripe_checkout_session(
            subscription_holder,
            price_id,
            request.user,
        )
        return Response(checkout_session.url)


@extend_schema(tags=["subscriptions"], exclude=True)
class CreatePortalSession(APIView):
    @extend_schema(
        operation_id="create_portal_session",
        request=None,
        responses={
            200: OpenApiTypes.URI,
        },
    )
    def post(self, request):
        subscription_holder = request.user
        try:
            portal_session = create_stripe_portal_session(subscription_holder)
            return Response(portal_session.url)
        except SubscriptionConfigError as e:
            return Response(str(e), status=500)


@extend_schema(tags=["subscriptions"])
class CheckUserSubscriptionAccess(APIView):
    """
    API endpoint to check if a user has access to a particular Stripe subscription.
    
    Query parameters:
    - username: The username (email) of the user to check
    - product_id: (optional) Stripe product ID to check access for
    - service_slug: (optional) Service slug to check access for
    
    You must provide either product_id or service_slug.
    """
    permission_classes = (IsAuthenticatedOrHasUserAPIKey,)

    @extend_schema(
        operation_id="check_user_subscription_access",
        parameters=[
            rest_framework.serializers.Serializer(
                name="CheckAccessParams",
                fields={
                    "username": rest_framework.serializers.CharField(
                        help_text="Username (email) of the user to check"
                    ),
                    "product_id": rest_framework.serializers.CharField(
                        required=False,
                        help_text="Stripe product ID to check access for"
                    ),
                    "service_slug": rest_framework.serializers.CharField(
                        required=False,
                        help_text="Service slug to check access for"
                    ),
                }
            )
        ],
        responses={
            200: inline_serializer(
                name="SubscriptionAccessResponse",
                fields={
                    "has_access": rest_framework.serializers.BooleanField(),
                    "username": rest_framework.serializers.CharField(),
                    "product_id": rest_framework.serializers.CharField(required=False),
                    "service_slug": rest_framework.serializers.CharField(required=False),
                    "subscription_details": rest_framework.serializers.DictField(required=False),
                }
            ),
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        },
    )
    def get(self, request):
        username = request.query_params.get("username")
        product_id = request.query_params.get("product_id")
        service_slug = request.query_params.get("service_slug")

        if not username:
            return Response(
                {"error": "username parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not product_id and not service_slug:
            return Response(
                {"error": "Either product_id or service_slug parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get the user by username (which is their email)
        try:
            user = CustomUser.objects.get(username=username)
        except CustomUser.DoesNotExist:
            return Response(
                {"error": f"User with username '{username}' not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        has_access = False
        subscription_details = None
        resolved_product_id = product_id
        resolved_service_slug = service_slug

        # Check access by product_id
        if product_id:
            # Check if user has any active subscriptions for this product
            if user.customer:
                subscription = Subscription.objects.filter(
                    customer=user.customer,
                    status__in=[
                        SubscriptionStatus.active,
                        SubscriptionStatus.trialing,
                        SubscriptionStatus.past_due
                    ]
                ).filter(
                    items__price__product__id=product_id
                ).first()
                
                if subscription:
                    has_access = True
                    # Get subscription details
                    try:
                        first_item = subscription.items.first()
                        product = first_item.price.product
                        subscription_details = {
                            "subscription_id": subscription.id,
                            "status": subscription.status,
                            "current_period_end": subscription.current_period_end.isoformat() if subscription.current_period_end else None,
                            "cancel_at_period_end": subscription.cancel_at_period_end,
                            "product_id": product.id,
                            "product_name": product.name,
                        }
                    except Exception:
                        pass

        # Check access by service_slug
        elif service_slug:
            has_access = user_has_service_access(user, service_slug)
            
            if has_access:
                try:
                    service = Service.objects.get(slug=service_slug, is_active=True)
                    resolved_product_id = service.stripe_product.id
                    
                    # Get subscription details
                    from apps.services.models import UserServiceAccess
                    access = UserServiceAccess.objects.filter(
                        user=user,
                        service=service,
                        is_active=True
                    ).first()
                    
                    if access and access.subscription:
                        subscription = access.subscription
                        subscription_details = {
                            "subscription_id": subscription.id,
                            "status": subscription.status,
                            "current_period_end": subscription.current_period_end.isoformat() if subscription.current_period_end else None,
                            "cancel_at_period_end": subscription.cancel_at_period_end,
                            "product_id": service.stripe_product.id,
                            "product_name": service.stripe_product.name,
                            "service_slug": service.slug,
                            "service_name": service.name,
                        }
                except Service.DoesNotExist:
                    return Response(
                        {"error": f"Service with slug '{service_slug}' not found"},
                        status=status.HTTP_404_NOT_FOUND
                    )
                except Exception:
                    pass

        response_data = {
            "has_access": has_access,
            "username": username,
        }
        
        if resolved_product_id:
            response_data["product_id"] = resolved_product_id
        if resolved_service_slug:
            response_data["service_slug"] = resolved_service_slug
        if subscription_details:
            response_data["subscription_details"] = subscription_details

        return Response(response_data, status=status.HTTP_200_OK)


@extend_schema(tags=["subscriptions"])
class UserServicesList(APIView):
    """
    API endpoint that returns a list of all services with subscription status for the authenticated user.
    
    Works with API keys - the API key must be associated with the user whose services you want to query.
    """
    permission_classes = (IsAuthenticatedOrHasUserAPIKey,)

    @extend_schema(
        operation_id="user_services_list",
        responses={
            200: inline_serializer(
                name="UserServicesResponse",
                fields={
                    "username": rest_framework.serializers.CharField(),
                    "services": rest_framework.serializers.ListField(
                        child=inline_serializer(
                            name="ServiceWithSubscription",
                            fields={
                                "service_id": rest_framework.serializers.IntegerField(),
                                "name": rest_framework.serializers.CharField(),
                                "slug": rest_framework.serializers.CharField(),
                                "description": rest_framework.serializers.CharField(required=False),
                                "has_access": rest_framework.serializers.BooleanField(),
                                "subscription": rest_framework.serializers.DictField(required=False),
                            }
                        )
                    ),
                }
            ),
            401: OpenApiTypes.OBJECT,
        },
    )
    def get(self, request):
        """
        Get all services with subscription status for the authenticated user.
        
        The user is determined from the API key or authenticated session.
        """
        user = request.user
        
        if not user.is_authenticated:
            return Response(
                {"error": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Get all active services
        all_services = Service.objects.filter(is_active=True).order_by('order', 'name')
        
        # Get user's service accesses
        user_accesses = {
            access.service_id: access
            for access in UserServiceAccess.objects.filter(
                user=user,
                is_active=True
            ).select_related('service', 'subscription')
        }
        
        # Get user's active subscriptions
        user_subscriptions = {}
        if user.customer:
            subscriptions = Subscription.objects.filter(
                customer=user.customer,
                status__in=[
                    SubscriptionStatus.active,
                    SubscriptionStatus.trialing,
                    SubscriptionStatus.past_due
                ]
            ).select_related('customer').prefetch_related('items__price__product')
            
            for subscription in subscriptions:
                for item in subscription.items.all():
                    product_id = item.price.product.id
                    if product_id not in user_subscriptions:
                        user_subscriptions[product_id] = subscription
        
        # Build response
        services_list = []
        for service in all_services:
            access = user_accesses.get(service.id)
            has_access = access.is_valid if access else False
            
            service_data = {
                "service_id": service.id,
                "name": service.name,
                "slug": service.slug,
                "description": service.description or "",
                "has_access": has_access,
            }
            
            # Add subscription details if user has access
            if has_access and access and access.subscription:
                subscription = access.subscription
                service_data["subscription"] = {
                    "subscription_id": subscription.id,
                    "status": subscription.status,
                    "current_period_end": subscription.current_period_end.isoformat() if subscription.current_period_end else None,
                    "cancel_at_period_end": subscription.cancel_at_period_end,
                    "product_id": service.stripe_product.id,
                    "product_name": service.stripe_product.name,
                }
            elif has_access and service.stripe_product.id in user_subscriptions:
                # Fallback: get subscription from user_subscriptions dict
                subscription = user_subscriptions[service.stripe_product.id]
                service_data["subscription"] = {
                    "subscription_id": subscription.id,
                    "status": subscription.status,
                    "current_period_end": subscription.current_period_end.isoformat() if subscription.current_period_end else None,
                    "cancel_at_period_end": subscription.cancel_at_period_end,
                    "product_id": service.stripe_product.id,
                    "product_name": service.stripe_product.name,
                }
            
            services_list.append(service_data)
        
        response_data = {
            "username": user.username,
            "services": services_list,
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
