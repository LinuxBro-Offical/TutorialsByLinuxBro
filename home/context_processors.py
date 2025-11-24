from django.conf import settings


def google_client_id(request):
    """Context processor to make Google Client ID available in all templates"""
    return {
        'GOOGLE_CLIENT_ID': getattr(settings, 'GOOGLE_CLIENT_ID', ''),
    }

