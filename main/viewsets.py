from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


class BaseModelViewSet(viewsets.ModelViewSet):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def response_success(self, data, status_code=status.HTTP_200_OK, message=None, metadata=None):
        
        try:
            response_data = {"results": data, "success": True, "status_code": status_code}
            if message:
                response_data["message"] = message
            if metadata:
                response_data["metadata"] = metadata
            return Response(response_data, status=status_code)
        except Exception as e:
            print("Error:: ", e)
            return self.response_error(str(e))

    def get_paginated_response(self, data, status_code=status.HTTP_200_OK, message=None, metadata=None):
        paginated_response = self.paginator.get_paginated_response(data)
        paginated_response.data["success"] = True
        paginated_response.data["status_code"] = status_code
        if message:
            paginated_response.data["message"] = message
        if metadata:
            paginated_response.data["metadata"] = metadata

        return paginated_response

    def response_error(self, data=None, status_code=status.HTTP_400_BAD_REQUEST, message=None, metadata=None):
        response_data = {"data": data, "success": False, "status_code": status_code}
        if message:
            response_data["message"] = message
        if metadata:
            response_data["metadata"] = metadata
        return Response(response_data, status=status_code)

    def response_unauthorized(self, data, status_code=status.HTTP_401_UNAUTHORIZED, message=None, metadata=None):
        response_data = {"data": data, "success": False, "status_code": status_code}
        if message:
            response_data["message"] = message
        if metadata:
            response_data["metadata"] = metadata
        return Response(response_data, status=status_code)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return self.response_success(
            serializer.data,
            status_code=status.HTTP_200_OK,
            message="Data retrieved successfully",
        )
        

class BaseViewSet(viewsets.ViewSet):
    def response_success(self, data, status_code=status.HTTP_200_OK, message=None, metadata=None):
        return BaseModelViewSet.response_success(self, data, status_code, message, metadata)
    
    def response_error(self, data, status_code=status.HTTP_400_BAD_REQUEST, message=None, metadata=None):
        return BaseModelViewSet.response_error(self, data, status_code, message, metadata)
    
    def response_unauthorized(self, data, status_code=status.HTTP_401_UNAUTHORIZED, message=None, metadata=None):
        return BaseModelViewSet.response_unauthorized(self, data, status_code, message, metadata)
    
    def get_paginated_response(self, data, status_code=status.HTTP_200_OK, message=None, metadata=None):
        return BaseModelViewSet.get_paginated_response(self, data, status_code, message, metadata)
    
    
class BaseAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    
    def response_success(self, data, status_code=status.HTTP_200_OK, message=None, metadata=None):
        return BaseModelViewSet.response_success(self, data, status_code, message, metadata)
    
    def response_error(self, data=None, status_code=status.HTTP_400_BAD_REQUEST, message=None, metadata=None):
        return BaseModelViewSet.response_error(self, data, status_code, message, metadata)
    
    def response_unauthorized(self, data, status_code=status.HTTP_401_UNAUTHORIZED, message=None, metadata=None):
        return BaseModelViewSet.response_unauthorized(self, data, status_code, message, metadata)
    
    def get_paginated_response(self, data, status_code=status.HTTP_200_OK, message=None, metadata=None):
        return BaseModelViewSet.get_paginated_response(self, data, status_code, message, metadata)
    

from payment.stripe_service import StripeService
# Webhook APIView
class StripeWebhookAPIView(BaseAPIView):
    def post(self, request):
        logger.info("Stripe webhook received:: %s", request.body)
        
        try:
            stripe_service = StripeService()
            event = stripe_service.construct_event(request.body, request.META.get("HTTP_STRIPE_SIGNATURE"))
            # logger.info("Stripe webhook event:: %s", event)
        except Exception as e:
            logger.error("error constructing event:: %s", e)
            return self.response_error(
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        
        # Handle gift card webhook
        from gift.services import GiftCardOnlinePaymentService
        GiftCardOnlinePaymentService(stripe_service).handle_stripe_event(event)

        # Handle subscription webhook
        from subscription.services import SubscriptionService
        SubscriptionService().handle_webhook_event(event)

        return self.response_success({"status": "success"})