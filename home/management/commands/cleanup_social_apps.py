from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp


class Command(BaseCommand):
    help = 'Removes duplicate social apps, ensuring only one per provider'

    def handle(self, *args, **options):
        site = Site.objects.get(id=1)
        
        providers = ['google', 'github', 'facebook', 'apple', 'twitter']
        
        total_removed = 0
        for provider in providers:
            apps = SocialApp.objects.filter(provider=provider)
            count = apps.count()
            
            if count > 1:
                # Keep the first one, delete the rest
                keep_app = apps.first()
                duplicates = apps.exclude(id=keep_app.id)
                removed_count = duplicates.count()
                duplicates.delete()
                total_removed += removed_count
                
                # Ensure site is linked
                if not keep_app.sites.filter(id=site.id).exists():
                    keep_app.sites.add(site)
                
                self.stdout.write(
                    self.style.WARNING(
                        f'{provider.capitalize()}: Removed {removed_count} duplicate(s), kept ID {keep_app.id}'
                    )
                )
            elif count == 1:
                app = apps.first()
                # Ensure site is linked
                if not app.sites.filter(id=site.id).exists():
                    app.sites.add(site)
                self.stdout.write(
                    self.style.SUCCESS(f'{provider.capitalize()}: OK (ID {app.id})')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'{provider.capitalize()}: No app found')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nRemoved {total_removed} duplicate social app(s).\n'
                'Each provider now has exactly one app.'
            )
        )
