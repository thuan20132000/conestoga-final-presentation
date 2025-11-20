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
from business.models import Business
from business.serializers import BusinessRolesSerializer
from main.viewsets import BaseModelViewSet
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.views import TokenVerifyView
class StaffViewSet(BaseModelViewSet):
    """ViewSet for Staff management"""
    queryset = Staff.objects.select_related('business')
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['business', 'role', 'is_active']
    search_fields = ['first_name', 'last_name', 'email', 'bio']
    ordering_fields = ['last_name', 'first_name', 'hire_date', 'created_at']
    ordering = ['last_name', 'first_name']
    
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
    
    @action(detail=True, methods=['get', 'post', 'delete'])
    def services(self, request, pk=None):
        """Manage staff services"""
        staff = self.get_object()
        
        if request.method == 'GET':
            staff_services = staff.staff_services.all()
            serializer = StaffServiceSerializer(staff_services, many=True)
            return Response(serializer.data)
        
        elif request.method == 'POST':
            service_id = request.data.get('service_id')
            is_primary = request.data.get('is_primary', False)
            
            if not service_id:
                return Response(
                    {'error': 'service_id is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate that the service exists and belongs to the same business
            try:
                from service.models import Service
                service = Service.objects.get(id=service_id, business=staff.business)
            except:
                return Response(
                    {'error': 'Service not found or does not belong to this business'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            staff_service, created = StaffService.objects.get_or_create(
                staff=staff, service_id=service_id, defaults={'is_primary': is_primary}
            )
            
            if not created:
                staff_service.is_primary = is_primary
                staff_service.save()
            
            serializer = StaffServiceSerializer(staff_service)
            return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
        
        elif request.method == 'DELETE':
            service_id = request.data.get('service_id')
            if not service_id:
                return Response(
                    {'error': 'service_id is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                staff_service = StaffService.objects.get(staff=staff, service_id=service_id)
                staff_service.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except StaffService.DoesNotExist:
                return Response(
                    {'error': 'Staff service not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
                
class StaffWorkingHoursViewSet(BaseModelViewSet):
    """ViewSet for Staff working hours"""
    queryset = StaffWorkingHours.objects.all()
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return StaffWorkingHoursCreateUpdateSerializer
        return StaffWorkingHoursSerializer
    
class StaffOffDayViewSet(BaseModelViewSet):
    """ViewSet for Staff off days"""
    queryset = StaffOffDay.objects.all()
    permission_classes = [AllowAny]

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
