from rest_framework import status, viewsets
from rest_framework.response import Response


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

    def response_error(self, data, status_code=status.HTTP_400_BAD_REQUEST, message=None, metadata=None):
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