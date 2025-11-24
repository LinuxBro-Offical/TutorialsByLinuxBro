from django.apps import AppConfig


class HomeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'home'

    def ready(self):
        """Called when Django starts - patch jwt module here as well"""
        # Import and call the patch function from __init__.py
        # This ensures jwt is patched after Django is fully initialized
        try:
            from home import _patch_jwt
            _patch_jwt()
        except ImportError:
            # If _patch_jwt is not available, try patching directly
            import sys
            try:
                import importlib
                jwt_module = importlib.import_module('jwt')
                from jwt.exceptions import PyJWTError
                jwt_module.PyJWTError = PyJWTError
                sys.modules['jwt'] = jwt_module
                if 'jwt' in sys.modules:
                    sys.modules['jwt'].PyJWTError = PyJWTError
            except (ImportError, AttributeError):
                pass
        
        # Patch Twitter OAuth2 adapter to use custom client with Content-Type header
        try:
            import allauth.socialaccount.providers.twitter_oauth2.views as twitter_views
            from home.twitter_oauth2_adapter import CustomTwitterOAuth2Adapter, oauth2_login, oauth2_callback
            
            # Replace the adapter and views
            twitter_views.TwitterOAuth2Adapter = CustomTwitterOAuth2Adapter
            twitter_views.oauth2_login = oauth2_login
            twitter_views.oauth2_callback = oauth2_callback
        except (ImportError, AttributeError) as e:
            # If patching fails, continue without it
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Could not patch Twitter OAuth2 adapter: {e}")