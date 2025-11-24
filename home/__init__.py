# JWT compatibility patch - must run before django-allauth imports jwt
# This ensures jwt.PyJWTError and jwt.decode are available for django-allauth
# This is critical for django-allauth's jwtkit module to work correctly
import sys

def _patch_jwt():
    """Patch jwt module - can be called multiple times safely"""
    try:
        # Force import of the actual PyJWT module
        import importlib
        jwt_module = importlib.import_module('jwt')
        
        # Import the exceptions first - this should always work
        from jwt.exceptions import PyJWTError
        
        # Ensure PyJWTError is available at the top level
        jwt_module.PyJWTError = PyJWTError
        
        # In PyJWT 2.x, decode and encode are already available as module-level attributes
        # They might be bound methods, but that's fine - they're still callable
        # We just need to ensure PyJWTError is available, which is the main issue
        
        # Store in sys.modules to prevent re-import issues
        # This ensures that any 'import jwt' statements get our patched version
        sys.modules['jwt'] = jwt_module
        
        # Also ensure that if jwt was already imported, we update it
        if 'jwt' in sys.modules:
            existing_jwt = sys.modules['jwt']
            existing_jwt.PyJWTError = PyJWTError
        
        return True
    except (ImportError, AttributeError) as e:
        # If jwt is not available, silently fail - it might not be installed
        # Only log if it's a critical error
        return False

# Patch immediately when this module is imported
_patch_jwt()

