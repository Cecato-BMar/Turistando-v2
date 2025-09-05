from django.conf import settings


def google_maps_api_key(request):
    """Make Google Maps API key available in all templates"""
    return {
        'GOOGLE_MAPS_API_KEY': getattr(settings, 'GOOGLE_MAPS_API_KEY', '')
    }

def notifications(request):
    """Make notifications available in all templates"""
    if hasattr(request, 'user') and request.user.is_authenticated:
        # Get notifications for business owners
        try:
            # Agora um usuário pode ter múltiplos negócios
            if hasattr(request.user, 'businesses'):
                # Contar notificações de todos os negócios do usuário
                unread_notifications = 0
                for business in request.user.businesses.all():
                    unread_notifications += business.notifications.filter(is_read=False).count()
                return {'unread_notifications': unread_notifications}
        except:
            pass
    return {'unread_notifications': 0}