from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    StaffViewSet, 
    StaffWorkingHoursViewSet, 
    StaffOffDayViewSet,
    RegisterView,
    LoginView,
    LogoutView,
    UserProfileView,
    TokenRefreshViewCustom,
    TokenVerifyViewCustom,
)
# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'staff', StaffViewSet, basename='staff')
router.register(r'working-hours', StaffWorkingHoursViewSet, basename='staff-working-hours')
router.register(r'off-days', StaffOffDayViewSet, basename='staff-off-days')

# The API URLs are now determined automatically by the router
urlpatterns = [
    path('', include(router.urls)),
    # Authentication endpoints
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/refresh/', TokenRefreshViewCustom.as_view(), name='token_refresh'),
    path('auth/verify/', TokenVerifyViewCustom.as_view(), name='token_verify'),
    path('auth/me/', UserProfileView.as_view(), name='user_profile'),
]
