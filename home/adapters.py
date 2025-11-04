from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth.models import User
from .models import Author
import uuid


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
    
    def pre_social_login(self, request, sociallogin):
        """Called before social login - auto signup if user exists"""
        # If user is already logged in, link the account
        if request.user.is_authenticated:
            sociallogin.connect(request, request.user)
        return super().pre_social_login(request, sociallogin)
    
    def populate_user(self, request, sociallogin, data):
        """Override to extract user data from social providers"""
        user = super().populate_user(request, sociallogin, data)
        
        # Extract name from social account
        if sociallogin.account.provider == 'google':
            user.first_name = data.get('given_name', '')
            user.last_name = data.get('family_name', '')
            user.email = data.get('email', '')
        elif sociallogin.account.provider == 'facebook':
            name = data.get('name', '').split(' ', 1)
            user.first_name = name[0] if len(name) > 0 else ''
            user.last_name = name[1] if len(name) > 1 else ''
            user.email = data.get('email', '')
        elif sociallogin.account.provider == 'github':
            name = data.get('name', '').split(' ', 1)
            user.first_name = name[0] if len(name) > 0 else ''
            user.last_name = name[1] if len(name) > 1 else ''
            user.email = data.get('email', '')
        elif sociallogin.account.provider == 'apple':
            user.first_name = data.get('firstName', '')
            user.last_name = data.get('lastName', '')
            user.email = data.get('email', '')
        elif sociallogin.account.provider == 'twitter':
            name = data.get('name', '').split(' ', 1)
            user.first_name = name[0] if len(name) > 0 else ''
            user.last_name = name[1] if len(name) > 1 else ''
            user.email = data.get('email', '')
        
        return user
    
    def save_user(self, request, sociallogin, form=None):
        """Override to create Author profile after social login"""
        user = super().save_user(request, sociallogin, form=form)
        
        # Create Author profile if it doesn't exist
        Author.objects.get_or_create(
            user=user,
            defaults={
                'full_name': user.get_full_name() or user.username,
                'uuid': uuid.uuid4()
            }
        )
        
        return user
