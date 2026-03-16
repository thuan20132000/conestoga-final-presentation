from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from business.models import Business
from main.viewsets import BaseAPIView, BaseViewSet
from payment.models import PaymentGateway, GatewayTypeType
from payment.stripe_service import StripeService
from staff.permissions import IsBusinessManager, IsBusinessManagerOrReceptionist
from django.conf import settings
from main.utils import country_name_to_code

class StripeConnectOnboardingView(BaseViewSet):
    """
    Create or reuse a Stripe Connect Express account for a business and
    return an onboarding link URL for the business owner to complete setup.
    """
    permission_classes = [IsAuthenticated, IsBusinessManager]
    
    def create(self, request):
        try:
            print(f"Request: {request.data}")
            business_id = request.query_params.get("business_id")
            print(f"Business ID: {business_id}")
            if not business_id:
                return self.response_error(
                    message="business_id is required",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

            try:
                business = Business.objects.get(id=business_id)
            except Business.DoesNotExist:
                return self.response_error(
                    message="Business not found",
                    status_code=status.HTTP_404_NOT_FOUND,
                )

            # Find or create Stripe payment gateway for this business
            gateway = (
                PaymentGateway.objects.filter(
                    business=business,
                    gateway_type=GatewayTypeType.STRIPE,
                )
                .order_by("-is_default", "name")
                .first()
            )

            if not gateway:
                gateway = PaymentGateway(
                    business=business,
                    name="Stripe",
                    gateway_type=GatewayTypeType.STRIPE,
                    is_active=True,
                    is_default=True,
                    test_mode=True,
                )

            previous_merchant_id = gateway.merchant_id

            # Create a new Connect account if one does not already exist
            if not gateway.merchant_id:
                account = StripeService.create_connect_account(
                    business_id=business.id,
                    email=business.email,
                    country=country_name_to_code(business.country),
                )
                gateway.merchant_id = account.id
                gateway.save()

            account_id = gateway.merchant_id

            # Build refresh and return URLs from settings or sensible defaults
            frontend_base_url = getattr(
                settings,
                "CALENDAR_LOGIN_URL",
                getattr(settings, "ONLINE_BOOKING_URL", "http://127.0.0.1:3001"),
            ).rstrip("/")

            refresh_url = getattr(
                settings,
                "STRIPE_CONNECT_REFRESH_URL",
                f"{frontend_base_url}/stripe/connect/refresh",
            )
            return_url = getattr(
                settings,
                "STRIPE_CONNECT_RETURN_URL",
                f"{frontend_base_url}/stripe/connect/complete",
            )

            account_link = StripeService.create_account_link(
                account_id=account_id,
                refresh_url=refresh_url,
                return_url=return_url,
            )

            response_data = {
                "stripe_account_id": account_id,
                "onboarding_url": account_link.url,
                "already_onboarded": bool(previous_merchant_id),
            }

            return self.response_success(
                response_data,
                status_code=status.HTTP_200_OK,
                message="Stripe Connect onboarding link created successfully",
            )
        except Exception as exc:
            return self.response_error(
                data={"error": str(exc)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Failed to create Stripe Connect onboarding link",
            )

