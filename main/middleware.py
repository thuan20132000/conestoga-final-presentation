from django.utils import timezone

class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Example: read from user profile or session
        # read the timezone from header 'X-Timezone'
        user_tz = request.headers.get('X-Timezone', 'UTC')
        
        timezone.activate(user_tz)
        print("user_tz", user_tz)
        print("timezone.now()", timezone.now())
        print("timezone.localtime(timezone.now())", timezone.localtime(timezone.now()))
        response = self.get_response(request)
        timezone.deactivate()
        return response