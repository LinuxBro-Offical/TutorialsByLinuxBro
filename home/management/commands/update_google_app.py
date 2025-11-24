from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
from decouple import config


class Command(BaseCommand):
    help = 'Updates Google social application with credentials from environment variables'

    def handle(self, *args, **options):
        site = Site.objects.get(id=1)
        
        google_client_id = config('GOOGLE_CLIENT_ID', default='')
        google_secret = config('GOOGLE_SECRET', default='')
        
        if not google_client_id or not google_secret:
            self.stdout.write(
                self.style.ERROR(
                    'ERROR: GOOGLE_CLIENT_ID and GOOGLE_SECRET must be set in your .env file!\n'
                    'Please add:\n'
                    'GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com\n'
                    'GOOGLE_SECRET=your-client-secret'
                )
            )
            return
        
        # Get or create Google social app
        app, created = SocialApp.objects.get_or_create(
            provider='google',
            defaults={
                'name': 'Google',
                'client_id': google_client_id,
                'secret': google_secret,
            }
        )
        
        # Update credentials if app already exists
        if not created:
            app.client_id = google_client_id
            app.secret = google_secret
            app.save()
            self.stdout.write(
                self.style.SUCCESS(f'Updated Google social app (ID: {app.id})')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Created Google social app (ID: {app.id})')
            )
        
        # Ensure site is linked
        if not app.sites.filter(id=site.id).exists():
            app.sites.add(site)
            self.stdout.write(self.style.SUCCESS('Linked site to Google app'))
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Google Client ID: {google_client_id[:20]}...\n'
                'Google authentication is now configured!'
            )
        )

