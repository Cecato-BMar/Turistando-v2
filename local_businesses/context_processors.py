from django.conf import settings
from django.contrib.auth.models import User

def google_maps_api_key(request):
    """Make Google Maps API key available in all templates"""
    return {
        'GOOGLE_MAPS_API_KEY': getattr(settings, 'GOOGLE_MAPS_API_KEY', '')
    }

def notifications(request):
    """Make notifications available in all templates"""
    if request.user.is_authenticated:
        # Get notifications for business owners
        try:
            if hasattr(request.user, 'business'):
                unread_notifications = request.user.business.notifications.filter(is_read=False).count()
                return {'unread_notifications': unread_notifications}
        except:
            pass
    return {'unread_notifications': 0}