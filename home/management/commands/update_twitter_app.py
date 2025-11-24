from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
from decouple import config


class Command(BaseCommand):
    help = 'Deletes old Twitter app and creates/updates Twitter OAuth2 social application with credentials from environment variables'

    def handle(self, *args, **options):
        site = Site.objects.get(id=1)
        
        twitter_client_id = config('TWITTER_CONSUMER_KEY', default='')
        twitter_secret = config('TWITTER_CONSUMER_SECRET', default='')
        
        if not twitter_client_id or not twitter_secret:
            self.stdout.write(
                self.style.ERROR(
                    'ERROR: TWITTER_CONSUMER_KEY and TWITTER_CONSUMER_SECRET must be set in your .env file!\n'
                    'Please add:\n'
                    'TWITTER_CONSUMER_KEY=your-consumer-key\n'
                    'TWITTER_CONSUMER_SECRET=your-consumer-secret'
                )
            )
            return
        
        # Step 1: Delete old Twitter app (provider='twitter')
        old_twitter_apps = SocialApp.objects.filter(provider='twitter')
        deleted_count = old_twitter_apps.count()
        if deleted_count > 0:
            for app in old_twitter_apps:
                self.stdout.write(
                    self.style.WARNING(f'Deleting old Twitter app (ID: {app.id}, Name: {app.name})')
                )
                app.delete()
            self.stdout.write(
                self.style.SUCCESS(f'✓ Deleted {deleted_count} old Twitter app(s)')
            )
        else:
            self.stdout.write(self.style.SUCCESS('No old Twitter apps found to delete'))
        
        # Step 2: Delete ALL Twitter-related apps first (to ensure clean state)
        # Delete any app with wrong provider names
        wrong_providers = ['twitter', 'twitter_oauth', 'x']
        for wrong_provider in wrong_providers:
            wrong_apps = SocialApp.objects.filter(provider=wrong_provider)
            if wrong_apps.exists():
                count = wrong_apps.count()
                wrong_apps.delete()
                self.stdout.write(
                    self.style.WARNING(f'Deleted {count} app(s) with wrong provider: {wrong_provider}')
                )
        
        # Step 3: Delete ALL existing twitter_oauth2 apps and recreate fresh
        # This ensures no stale data or provider_id mismatches
        existing_twitter_oauth2 = SocialApp.objects.filter(provider='twitter_oauth2')
        if existing_twitter_oauth2.exists():
            count = existing_twitter_oauth2.count()
            existing_twitter_oauth2.delete()
            self.stdout.write(
                self.style.WARNING(f'Deleted {count} existing Twitter OAuth2 app(s) to recreate fresh')
            )
        
        # Step 4: Create NEW Twitter OAuth2 app with EXACT values
        app = SocialApp.objects.create(
            provider='twitter_oauth2',  # MUST be exactly 'twitter_oauth2'
            provider_id='twitter_oauth2',  # Set provider_id to match provider
            name='Twitter OAuth2',  # MUST be exactly 'Twitter OAuth2'
            client_id=twitter_client_id,
            secret=twitter_secret,
        )
        self.stdout.write(
            self.style.SUCCESS(f'Created fresh Twitter OAuth2 social app (ID: {app.id})')
        )
        
        # Verify the app is correct
        app.refresh_from_db()
        checks = [
            ('Provider is "twitter_oauth2"', app.provider == 'twitter_oauth2'),
            ('Provider ID is "twitter_oauth2"', app.provider_id == 'twitter_oauth2'),
            ('Name is "Twitter OAuth2"', app.name == 'Twitter OAuth2'),
        ]
        
        all_passed = True
        for check_name, check_result in checks:
            status = '✓' if check_result else '✗'
            self.stdout.write(f'{status} {check_name}')
            if not check_result:
                all_passed = False
        
        if not all_passed:
            self.stdout.write(
                self.style.ERROR(
                    f'\n✗ VERIFICATION FAILED!\n'
                    f'  Provider="{app.provider}" (should be "twitter_oauth2")\n'
                    f'  Provider ID="{app.provider_id}" (should be "twitter_oauth2")\n'
                    f'  Name="{app.name}" (should be "Twitter OAuth2")'
                )
            )
        
        # Ensure site is linked
        if not app.sites.filter(id=site.id).exists():
            app.sites.add(site)
            self.stdout.write(self.style.SUCCESS('Linked site to Twitter OAuth2 app'))
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Twitter Client ID: {twitter_client_id[:20]}...\n'
                'Twitter OAuth2 authentication is now configured!'
            )
        )

