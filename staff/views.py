from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import authenticate
from .models import Staff, StaffService, StaffWorkingHours, StaffOffDay
from .serializers import (
    StaffSerializer,
    StaffCreateUpdateSerializer,
    StaffServiceSerializer,
    StaffWorkingHoursSerializer,
    StaffWorkingHoursCreateUpdateSerializer,
    StaffOffDaySerializer,
    StaffOffDayCreateUpdateSerializer,
    LoginSerializer,
    RegisterSerializer,
    UserProfileSerializer,
)
from django_filters import rest_framework as filters
from business.serializers import BusinessRolesSerializer
from main.viewsets import BaseModelViewSet
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.views import TokenVerifyView
from staff.permissions import IsBusinessManager

class StaffFilter(filters.FilterSet):
    """Filter for Staff"""
    business_id = filters.NumberFilter(field_name='business_id', lookup_expr='exact', required=True)
    role_name = filters.CharFilter(field_name='role__name', lookup_expr='exact', required=False)
    is_payment_processing_allowed = filters.BooleanFilter(field_name='is_payment_processing_allowed', lookup_expr='exact', required=False)
    class Meta:
        model = Staff
        fields = ['business_id', 'role_name', 'is_payment_processing_allowed']

class StaffViewSet(BaseModelViewSet):
    """ViewSet for Staff management"""
    queryset = Staff.objects.filter(is_deleted=False)
    permission_classes = [IsAuthenticated, IsBusinessManager]
    filterset_class = StaffFilter
    
    def list(self, request, *args, **kwargs):
        """List staff"""
        try:
            queryset = self.filter_queryset(self.queryset.filter(business_id=request.user.business_id))
            serializer = StaffSerializer(queryset, many=True)
            return self.response_success(serializer.data)
        except Exception as e:
            return self.response_error(str(e))

    def destroy(self, request, *args, **kwargs):
        """Destroy a staff"""
        try:
            instance = self.get_object()
            instance.soft_delete()
            return self.response_success(data=None, message="Staff deleted successfully")
        except Exception as e:
            return self.response_error(str(e))
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return StaffCreateUpdateSerializer
        return StaffSerializer
    
    @action(detail=True, methods=['get'])
    def roles(self, request, pk=None):
        """Get staff roles"""
        staff = self.get_object()
        roles = staff.role
        serializer = BusinessRolesSerializer(roles, many=True)
        return self.response_success(serializer.data)

    @action(detail=True, methods=['get'], url_path='working-hours')
    def working_hours(self, request, pk=None):
        """Get staff working hours"""
        staff = self.get_object()
        print("staff", staff)
        working_hours = staff.working_hours.all()
        print("working_hours", working_hours)
        serializer = StaffWorkingHoursSerializer(working_hours, many=True)
        return self.response_success(serializer.data)
    
    @action(detail=True, methods=['get'], url_path='off-days')
    def off_days(self, request, pk=None):
        """Get staff off days"""
        staff = self.get_object()
        off_days = staff.staff_off_days.all()
        serializer = StaffOffDaySerializer(off_days, many=True)
        return self.response_success(serializer.data)
    
    @action(detail=True, methods=['get'], url_path='services')
    def services(self, request, pk=None):
        """Get staff services"""
        try:
            staff = self.get_object()
            if not staff:
                return self.response_error(
                    {'error': 'Staff not found'}, 
                    status_code=status.HTTP_404_NOT_FOUND
                )
            services = staff.staff_services.all()
            serializer = StaffServiceSerializer(services, many=True)
            return self.response_success(serializer.data)
        except Exception as e:
            return self.response_error(str(e))
                
class StaffServiceViewSet(BaseModelViewSet):
    """ViewSet for Staff services"""
    queryset = StaffService.objects.all()
    permission_classes = [IsAuthenticated, IsBusinessManager]

    def get_serializer_class(self):
        return StaffServiceSerializer
    
    def partial_update(self, request, *args, **kwargs):
        """Partial update staff service"""
        try:
            instance = self.get_object()
            serializer = StaffServiceSerializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            instance = serializer.save()
            return self.response_success(StaffServiceSerializer(instance).data)
        except Exception as e:
            return self.response_error(str(e))
    
class StaffWorkingHoursViewSet(BaseModelViewSet):
    """ViewSet for Staff working hours"""
    queryset = StaffWorkingHours.objects.all()
    permission_classes = [IsAuthenticated, IsBusinessManager]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return StaffWorkingHoursCreateUpdateSerializer
        return StaffWorkingHoursSerializer
    
class StaffOffDayViewSet(BaseModelViewSet):
    """ViewSet for Staff off days"""
    queryset = StaffOffDay.objects.all()
    permission_classes = [IsAuthenticated, IsBusinessManager]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return StaffOffDayCreateUpdateSerializer
        return StaffOffDaySerializer


class RegisterView(APIView):
    """View for user registration"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            serializer = RegisterSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.save()
                refresh = RefreshToken.for_user(user)
                
                return Response({
                    'success': True,
                    'message': 'Registration successful',
                    'results': {
                        'user': StaffSerializer(user).data,
                        'tokens': {
                            'refresh': str(refresh),
                            'access': str(refresh.access_token),
                        }
                    }
                }, status=status.HTTP_201_CREATED)
            
            return Response({
                'success': False,
                'message': 'Registration failed',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Error during registration',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """View for user login and JWT token generation"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            serializer = LoginSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.validated_data['user']
                refresh = RefreshToken.for_user(user)
                
                return Response({
                    'success': True,
                    'message': 'Login successful',
                    'results': {
                        'user': UserProfileSerializer(user).data,
                        'tokens': {
                            'refresh': str(refresh),
                            'access': str(refresh.access_token),
                        }
                    }
                }, status=status.HTTP_200_OK)
            
            return Response({
                'success': False,
                'message': 'Invalid credentials',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Error during login',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """View for user logout (token blacklisting)"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                try:
                    token = RefreshToken(refresh_token)
                    # Try to blacklist if blacklist app is installed
                    try:
                        token.blacklist()
                    except AttributeError:
                        # Blacklist not enabled, just invalidate the token
                        pass
                except Exception as token_error:
                    # Token might already be invalid/blacklisted
                    pass
            
            return Response({
                'success': True,
                'message': 'Logout successful'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Error during logout',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    """View to get current user profile"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    def put(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Profile updated successfully',
                'results': serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'message': 'Error updating profile',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class TokenRefreshViewCustom(TokenRefreshView):
    """Custom token refresh view with better response format"""
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            return Response({
                'success': True,
                'message': 'Token refreshed successfully',
                'results': response.data
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'message': 'Token refresh failed',
            'errors': response.data
        }, status=response.status_code)
    

class TokenVerifyViewCustom(TokenVerifyView):
    """Custom token verify view with better response format"""
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        try:
            token = request.data.get('token')
            if not token:
                return Response({
                    'success': False,
                    'message': 'Token is required',
                    'error': 'Token is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            response = super().post(request, *args, **kwargs)
            return Response({
                'success': True,
                'message': 'Token verified successfully',
                'results': response.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Error during token verification',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
