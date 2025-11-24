from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
from decouple import config


class Command(BaseCommand):
    help = 'AGGRESSIVELY deletes ALL Twitter/X apps and creates a fresh Twitter OAuth2 app'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force deletion without confirmation',
        )

    def handle(self, *args, **options):
        site = Site.objects.get(id=1)
        
        twitter_client_id = config('TWITTER_CONSUMER_KEY', default='')
        twitter_secret = config('TWITTER_CONSUMER_SECRET', default='')
        
        if not twitter_client_id or not twitter_secret:
            self.stdout.write(
                self.style.ERROR(
                    'ERROR: TWITTER_CONSUMER_KEY and TWITTER_CONSUMER_SECRET must be set in your .env file!'
                )
            )
            return
        
        self.stdout.write(self.style.WARNING('\n=== AGGRESSIVE TWITTER APP CLEANUP ===\n'))
        
        # Step 1: Find ALL apps that might be Twitter-related
        all_apps = SocialApp.objects.all()
        twitter_apps_to_delete = []
        
        for app in all_apps:
            provider_lower = (app.provider or '').lower()
            name_lower = (app.name or '').lower()
            
            # Check if it's Twitter/X related
            is_twitter = (
                'twitter' in provider_lower or
                'x' in provider_lower or
                'twitter' in name_lower or
                (name_lower and 'x' in name_lower and 'oauth' in name_lower)
            )
            
            if is_twitter:
                twitter_apps_to_delete.append(app)
        
        if not twitter_apps_to_delete:
            self.stdout.write(self.style.SUCCESS('No Twitter/X apps found to delete'))
        else:
            self.stdout.write(f'Found {len(twitter_apps_to_delete)} Twitter/X app(s) to delete:')
            for app in twitter_apps_to_delete:
                self.stdout.write(
                    self.style.WARNING(
                        f'  ID {app.id}: Provider="{app.provider}", Name="{app.name}", Provider ID="{app.provider_id}"'
                    )
                )
            
            # Delete them all
            deleted_ids = [app.id for app in twitter_apps_to_delete]
            for app in twitter_apps_to_delete:
                app.delete()
            
            self.stdout.write(
                self.style.SUCCESS(f'\n✓ Deleted {len(twitter_apps_to_delete)} app(s): IDs {deleted_ids}')
            )
        
        # Step 2: Double-check - delete by exact provider values (case-insensitive)
        exact_providers_to_delete = [
            'twitter',
            'Twitter',
            'TWITTER',
            'twitter_oauth',
            'twitter_oauth2',
            'Twitter OAuth2',
            'x',
            'X',
            'X (Twitter)',
        ]
        
        for provider_value in exact_providers_to_delete:
            apps = SocialApp.objects.filter(provider=provider_value)
            if apps.exists():
                count = apps.count()
                app_ids = list(apps.values_list('id', flat=True))
                apps.delete()
                self.stdout.write(
                    self.style.WARNING(
                        f'Deleted {count} app(s) with provider="{provider_value}": IDs {app_ids}'
                    )
                )
        
        # Step 3: Create FRESH Twitter OAuth2 app with EXACT values
        self.stdout.write(self.style.SUCCESS('\n=== Creating Fresh Twitter OAuth2 App ===\n'))
        
        app = SocialApp.objects.create(
            provider='twitter_oauth2',  # MUST be exactly 'twitter_oauth2'
            provider_id='twitter_oauth2',  # MUST match provider
            name='Twitter OAuth2',  # MUST be exactly 'Twitter OAuth2'
            client_id=twitter_client_id,
            secret=twitter_secret,
        )
        
        # Link to site
        app.sites.add(site)
        
        # Refresh and verify
        app.refresh_from_db()
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created Twitter OAuth2 app (ID: {app.id})'))
        self.stdout.write(f'\n=== Verification ===')
        self.stdout.write(f'  Provider: "{app.provider}" (should be "twitter_oauth2")')
        self.stdout.write(f'  Provider ID: "{app.provider_id}" (should be "twitter_oauth2")')
        self.stdout.write(f'  Name: "{app.name}" (should be "Twitter OAuth2")')
        self.stdout.write(f'  Client ID: {app.client_id[:30]}...')
        self.stdout.write(f'  Has Secret: {bool(app.secret)}')
        self.stdout.write(f'  Linked to Site: {app.sites.filter(id=site.id).exists()}')
        
        # Final check
        if app.provider == 'twitter_oauth2' and app.provider_id == 'twitter_oauth2' and app.name == 'Twitter OAuth2':
            self.stdout.write(
                self.style.SUCCESS('\n✓✓✓ VERIFICATION PASSED - App is correctly configured! ✓✓✓')
            )
        else:
            self.stdout.write(
                self.style.ERROR(
                    '\n✗✗✗ VERIFICATION FAILED - App configuration is incorrect! ✗✗✗'
                )
            )
        
        # Final count
        remaining_twitter_apps = SocialApp.objects.filter(provider='twitter_oauth2')
        if remaining_twitter_apps.count() == 1:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✓ Perfect! Only 1 Twitter OAuth2 app exists (ID: {app.id})'
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR(
                    f'\n✗ WARNING: {remaining_twitter_apps.count()} Twitter OAuth2 app(s) exist!'
                )
            )

