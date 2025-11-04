from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
from decouple import config


class Command(BaseCommand):
    help = 'Creates placeholder social applications for development/testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Remove duplicate social apps before creating new ones',
        )

    def handle(self, *args, **options):
        site = Site.objects.get(id=1)
        
        providers = [
            ('google', 'Google', 
             config('GOOGLE_CLIENT_ID', default='YOUR_GOOGLE_CLIENT_ID'),
             config('GOOGLE_SECRET', default='YOUR_GOOGLE_SECRET')),
            ('github', 'GitHub',
             config('GITHUB_CLIENT_ID', default='YOUR_GITHUB_CLIENT_ID'),
             config('GITHUB_SECRET', default='YOUR_GITHUB_SECRET')),
            ('facebook', 'Facebook',
             config('FACEBOOK_APP_ID', default='YOUR_FACEBOOK_APP_ID'),
             config('FACEBOOK_SECRET', default='YOUR_FACEBOOK_SECRET')),
            ('apple', 'Apple',
             config('APPLE_CLIENT_ID', default='YOUR_APPLE_SERVICE_ID'),
             config('APPLE_SECRET', default='YOUR_APPLE_SECRET')),
            ('twitter', 'Twitter/X',
             config('TWITTER_CONSUMER_KEY', default='YOUR_TWITTER_CONSUMER_KEY'),
             config('TWITTER_CONSUMER_SECRET', default='YOUR_TWITTER_CONSUMER_SECRET')),
        ]
        
        if options['clean']:
            # Remove all existing social apps
            SocialApp.objects.all().delete()
            self.stdout.write(self.style.WARNING('Removed all existing social apps'))
        
        created_count = 0
        for provider, name, client_id, secret in providers:
            # Check if app exists for this provider
            existing_apps = SocialApp.objects.filter(provider=provider)
            
            if existing_apps.exists():
                # Keep only the first one, delete duplicates
                app = existing_apps.first()
                duplicates = existing_apps.exclude(id=app.id)
                if duplicates.exists():
                    duplicates.delete()
                    self.stdout.write(
                        self.style.WARNING(f'Removed duplicate {name} apps, keeping ID: {app.id}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'{name} social app already exists (ID: {app.id})')
                    )
            else:
                # Create new app
                app = SocialApp.objects.create(
                    provider=provider,
                    name=name,
                    client_id=client_id,
                    secret=secret,
                )
                app.sites.add(site)
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created {name} social app (placeholder credentials)')
                )
            # Ensure site is linked (in case it wasn't linked before)
            if not app.sites.filter(id=site.id).exists():
                app.sites.add(site)
                self.stdout.write(
                    self.style.WARNING(f'Added site to {name} app')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nCreated {created_count} social application(s).\n'
                'Please update the credentials in Django Admin → Social Applications → Social Applications'
            )
        )
