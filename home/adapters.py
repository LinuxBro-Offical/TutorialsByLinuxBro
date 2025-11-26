from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth.models import User
from .models import Author
import uuid
import logging

logger = logging.getLogger(__name__)


class AccountAdapter(DefaultAccountAdapter):
    """Custom adapter for regular account signups"""
    
    def save_user(self, request, user, form, commit=True):
        """Override to create Author profile"""
        user = super().save_user(request, user, form, commit=commit)
        if commit:
            # Create Author profile if it doesn't exist
            Author.objects.get_or_create(
                user=user,
                defaults={
                    'full_name': user.get_full_name() or user.username,
                    'uuid': uuid.uuid4()
                }
            )
        return user


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    """Custom adapter for social account signups"""
    
    def is_auto_signup_allowed(self, request, sociallogin):
        """Allow automatic signup without confirmation"""
        return True
    
    def on_authentication_error(self, request, provider, error=None, exception=None, extra_context=None):
        """Handle authentication errors - log them for debugging"""
        logger.error(
            f"Social authentication error for {provider}: {error}",
            exc_info=exception
        )
        # Call parent to maintain default behavior
        return super().on_authentication_error(request, provider, error, exception, extra_context)
    
    def pre_social_login(self, request, sociallogin):
        """Called before social login - auto signup if user exists"""
        
        # If user is already logged in, link the account
        if request.user.is_authenticated:
            try:
                sociallogin.connect(request, request.user)
                return
            except Exception as e:
                logger.warning(f"Error connecting social account to logged-in user: {str(e)}", exc_info=True)
                # Continue with normal flow - might be trying to link duplicate account
        
        # Check if a user with this email already exists
        email = None
        if sociallogin.email_addresses:
            email = sociallogin.email_addresses[0].email
        
        if email:
            try:
                existing_user = User.objects.get(email=email)
                # Check if this social account is already linked to a different user
                from allauth.socialaccount.models import SocialAccount
                try:
                    existing_social = SocialAccount.objects.get(
                        provider=sociallogin.account.provider if hasattr(sociallogin, 'account') else 'google',
                        uid=sociallogin.account.uid if hasattr(sociallogin, 'account') else None
                    )
                    # If already linked to this user, just proceed
                    if existing_social.user == existing_user:
                        return super().pre_social_login(request, sociallogin)
                    # If linked to different user, don't try to connect
                    logger.warning(f"Social account already linked to different user")
                except SocialAccount.DoesNotExist:
                    # Not linked yet, try to connect
                    try:
                        sociallogin.connect(request, existing_user)
                        return
                    except Exception as e:
                        logger.warning(f"Error connecting social account to existing user: {str(e)}", exc_info=True)
                        # Continue with normal flow if connection fails
            except User.DoesNotExist:
                pass
            except User.MultipleObjectsReturned:
                # If multiple users exist, use the first one
                existing_user = User.objects.filter(email=email).first()
                if existing_user:
                    try:
                        sociallogin.connect(request, existing_user)
                        return
                    except Exception as e:
                        logger.warning(f"Error connecting to first user with email {email}: {str(e)}", exc_info=True)
        
        return super().pre_social_login(request, sociallogin)
    
    def populate_user(self, request, sociallogin, data):
        """Override to extract user data from social providers"""
        user = super().populate_user(request, sociallogin, data)
        
        # Get provider name safely
        try:
            provider = sociallogin.account.provider if hasattr(sociallogin, 'account') and sociallogin.account else None
        except:
            provider = getattr(sociallogin, 'provider', None)
        
        # Extract name from social account
        if provider == 'google':
            user.first_name = data.get('given_name', '') or ''
            user.last_name = data.get('family_name', '') or ''
            email = data.get('email', '')
            if email:
                user.email = email
                # Ensure username is set if not already set
                if not user.username:
                    # Use email as username base
                    username_base = email.split('@')[0]
                    # Make sure username is unique
                    username = username_base
                    counter = 1
                    while User.objects.filter(username=username).exists():
                        username = f"{username_base}{counter}"
                        counter += 1
                    user.username = username
            # If no email, ensure username is still set
            elif not user.username:
                # Generate username from name or use a default
                name_parts = [user.first_name, user.last_name]
                name = ''.join([p for p in name_parts if p]).lower().replace(' ', '')
                if name:
                    username = name
                    counter = 1
                    while User.objects.filter(username=username).exists():
                        username = f"{name}{counter}"
                        counter += 1
                else:
                    username = f"user_{sociallogin.account.uid[:8]}" if hasattr(sociallogin, 'account') and hasattr(sociallogin.account, 'uid') else f"user_{uuid.uuid4().hex[:8]}"
                    counter = 1
                    while User.objects.filter(username=username).exists():
                        username = f"user_{uuid.uuid4().hex[:8]}"
                user.username = username
        elif provider == 'facebook':
            name = data.get('name', '').split(' ', 1)
            user.first_name = name[0] if len(name) > 0 else ''
            user.last_name = name[1] if len(name) > 1 else ''
            email = data.get('email', '')
            if email:
                user.email = email
        elif provider == 'github':
            name = data.get('name', '').split(' ', 1)
            user.first_name = name[0] if len(name) > 0 else ''
            user.last_name = name[1] if len(name) > 1 else ''
            email = data.get('email', '')
            if email:
                user.email = email
        elif provider == 'apple':
            user.first_name = data.get('firstName', '') or ''
            user.last_name = data.get('lastName', '') or ''
            email = data.get('email', '')
            if email:
                user.email = email
        elif provider == 'twitter':
            name = data.get('name', '').split(' ', 1)
            user.first_name = name[0] if len(name) > 0 else ''
            user.last_name = name[1] if len(name) > 1 else ''
            email = data.get('email', '')
            if email:
                user.email = email
        
        return user
    
    def save_user(self, request, sociallogin, form=None):
        """Override to create Author profile after social login"""
        user = super().save_user(request, sociallogin, form=form)
        
        # Create Author profile if it doesn't exist (in a separate try-except to not break login)
        try:
            full_name = user.get_full_name() or user.username or (user.email.split('@')[0] if user.email else 'User')
            author, created = Author.objects.get_or_create(
            user=user,
            defaults={
                    'full_name': full_name,
                'uuid': uuid.uuid4()
            }
        )
            
            # Download and save profile picture from social account if available
            # Only download if author doesn't already have a profile picture
            if sociallogin.account and not author.profile_picture:
                try:
                    # Get picture URL from social account extra_data
                    picture_url = None
                    provider = sociallogin.account.provider
                    
                    if provider == 'google':
                        picture_url = sociallogin.account.extra_data.get('picture')
                    elif provider == 'facebook':
                        picture_url = sociallogin.account.extra_data.get('picture', {}).get('data', {}).get('url')
                        if not picture_url:
                            picture_url = sociallogin.account.extra_data.get('picture')
                    elif provider == 'github':
                        picture_url = sociallogin.account.extra_data.get('avatar_url')
                    elif provider == 'twitter_oauth2':
                        # Twitter OAuth2 uses profile_image_url (may have _normal suffix)
                        picture_url = sociallogin.account.extra_data.get('profile_image_url')
                        # Remove _normal, _bigger, etc. to get original size
                        if picture_url:
                            picture_url = picture_url.replace('_normal', '').replace('_bigger', '').replace('_mini', '')
                    elif provider == 'twitter':
                        # Legacy Twitter OAuth1.0a
                        picture_url = sociallogin.account.extra_data.get('profile_image_url_https')
                    elif provider == 'apple':
                        # Apple doesn't provide profile pictures
                        picture_url = None
                    
                    # Download and save the profile picture
                    if picture_url:
                        import requests
                        from django.core.files.base import ContentFile
                        
                        try:
                            # Download the image
                            response = requests.get(picture_url, timeout=10)
                            response.raise_for_status()
                            
                            # Get file extension from URL or content type
                            content_type = response.headers.get('content-type', '')
                            if 'image/jpeg' in content_type or 'image/jpg' in content_type:
                                ext = 'jpg'
                            elif 'image/png' in content_type:
                                ext = 'png'
                            elif 'image/gif' in content_type:
                                ext = 'gif'
                            elif 'image/webp' in content_type:
                                ext = 'webp'
                            else:
                                # Try to get from URL
                                if '.jpg' in picture_url or '.jpeg' in picture_url:
                                    ext = 'jpg'
                                elif '.png' in picture_url:
                                    ext = 'png'
                                elif '.gif' in picture_url:
                                    ext = 'gif'
                                else:
                                    ext = 'jpg'  # Default to jpg
                            
                            # Create filename (don't include directory, it's handled by upload_to)
                            filename = f"{user.username}_{uuid.uuid4().hex[:8]}.{ext}"
                            
                            # Save the image
                            author.profile_picture.save(
                                filename,
                                ContentFile(response.content),
                                save=True
                            )
                        except (requests.RequestException, IOError, OSError) as e:
                            logger.warning(f"Could not download profile picture from {picture_url}: {str(e)}")
                except Exception as e:
                    logger.warning(f"Could not save profile picture for user {user.username}: {str(e)}", exc_info=True)
                    
        except Exception as e:
            logger.warning(f"Could not create Author profile for user {user.username}: {str(e)}", exc_info=True)
            # Continue - user is still logged in, Author can be created later
        
        return user
