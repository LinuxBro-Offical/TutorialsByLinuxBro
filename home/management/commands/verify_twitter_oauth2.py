from django.core.management.base import BaseCommand
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site
from django.test import RequestFactory


class Command(BaseCommand):
    help = 'Verifies Twitter OAuth2 configuration and provides troubleshooting information'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n=== Twitter OAuth2 Configuration Verification ===\n'))
        
        # Check app in database
        twitter_app = SocialApp.objects.filter(provider='twitter_oauth2').first()
        if not twitter_app:
            self.stdout.write(self.style.ERROR('✗ No Twitter OAuth2 app found in database!'))
            self.stdout.write(self.style.WARNING('  Run: python manage.py update_twitter_app'))
            return
        
        self.stdout.write(self.style.SUCCESS('✓ Twitter OAuth2 app found in database'))
        self.stdout.write(f'  ID: {twitter_app.id}')
        self.stdout.write(f'  Provider: {twitter_app.provider}')
        self.stdout.write(f'  Name: {twitter_app.name}')
        self.stdout.write(f'  Client ID: {twitter_app.client_id[:30]}...')
        self.stdout.write(f'  Has Secret: {bool(twitter_app.secret)}')
        
        # Check site
        site = Site.objects.get(id=1)
        if twitter_app.sites.filter(id=site.id).exists():
            self.stdout.write(self.style.SUCCESS(f'✓ Linked to site: {site.domain}'))
        else:
            self.stdout.write(self.style.ERROR(f'✗ NOT linked to site: {site.domain}'))
        
        # Check adapter
        try:
            from allauth.socialaccount.providers.twitter_oauth2.views import TwitterOAuth2Adapter
            factory = RequestFactory()
            request = factory.get('/')
            request.META['HTTP_HOST'] = site.domain
            
            adapter = TwitterOAuth2Adapter(request)
            self.stdout.write(self.style.SUCCESS('\n✓ TwitterOAuth2Adapter loaded correctly'))
            self.stdout.write(f'  Provider ID: {adapter.provider_id}')
            self.stdout.write(f'  Basic Auth: {adapter.basic_auth}')
            self.stdout.write(f'  Access Token URL: {adapter.access_token_url}')
            
            if adapter.basic_auth:
                self.stdout.write(self.style.SUCCESS('  ✓ Basic Auth is enabled (required for Twitter OAuth2)'))
            else:
                self.stdout.write(self.style.ERROR('  ✗ Basic Auth is NOT enabled!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Error loading adapter: {e}'))
        
        # Check callback URL
        from django.urls import reverse
        try:
            callback_url = reverse('twitter_oauth2_callback')
            full_callback = f"http://{site.domain}{callback_url}"
            self.stdout.write(self.style.SUCCESS(f'\n✓ Callback URL: {full_callback}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Error getting callback URL: {e}'))
        
        # Troubleshooting checklist
        self.stdout.write(self.style.WARNING('\n=== Twitter Developer Portal Checklist ==='))
        self.stdout.write('Go to: https://developer.twitter.com/en/portal/projects-and-apps')
        self.stdout.write('\n1. App Type:')
        self.stdout.write('   □ Must be "OAuth2.0" (NOT "OAuth1.0a")')
        self.stdout.write('   □ If you only see OAuth1.0a, create a NEW OAuth2.0 app')
        self.stdout.write('\n2. App Settings:')
        self.stdout.write('   □ App permissions: Read (at minimum)')
        self.stdout.write(f'   □ Callback URL: http://{site.domain}/accounts/twitter_oauth2/login/callback/')
        self.stdout.write('   □ Type of App: Web App')
        self.stdout.write('\n3. Credentials:')
        self.stdout.write('   □ Use "OAuth2.0 Client ID" (NOT "API Key")')
        self.stdout.write('   □ Use "OAuth2.0 Client Secret" (NOT "API Secret")')
        self.stdout.write('   □ OAuth2.0 Client IDs are typically 20-40 characters, no colons')
        self.stdout.write('\n4. Common Mistakes:')
        self.stdout.write('   ✗ Using OAuth1.0a API Key/Secret with OAuth2.0 → "unauthorized_client"')
        self.stdout.write('   ✗ Wrong callback URL → "redirect_uri_mismatch"')
        self.stdout.write('   ✗ Missing callback URL in Twitter portal → "unauthorized_client"')
        self.stdout.write('   ✗ App not set to OAuth2.0 → "Missing valid authorization header"')
        
        self.stdout.write(self.style.SUCCESS('\n=== Verification Complete ===\n'))

