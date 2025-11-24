from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from home.models import Author
from allauth.socialaccount.models import SocialAccount
import requests
from django.core.files.base import ContentFile
import uuid


class Command(BaseCommand):
    help = 'Downloads and saves profile pictures from social accounts for users who don\'t have one'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Update profile picture for a specific username',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Update profile pictures for all users with social accounts',
        )

    def handle(self, *args, **options):
        if options['username']:
            users = User.objects.filter(username=options['username'])
        elif options['all']:
            # Get all users with social accounts who don't have profile pictures
            social_users = SocialAccount.objects.all().values_list('user_id', flat=True)
            users = User.objects.filter(
                id__in=social_users,
                author__profile_picture__isnull=True
            )
        else:
            self.stdout.write(self.style.ERROR('Please specify --username or --all'))
            return

        updated_count = 0
        error_count = 0

        for user in users:
            try:
                if not hasattr(user, 'author'):
                    self.stdout.write(self.style.WARNING(f'User {user.username} has no Author profile'))
                    continue

                author = user.author
                if author.profile_picture:
                    self.stdout.write(self.style.WARNING(f'User {user.username} already has a profile picture'))
                    continue

                # Get social account
                social = SocialAccount.objects.filter(user=user).first()
                if not social:
                    self.stdout.write(self.style.WARNING(f'User {user.username} has no social account'))
                    continue

                # Get picture URL based on provider
                picture_url = None
                provider = social.provider

                if provider == 'google':
                    picture_url = social.extra_data.get('picture')
                elif provider == 'facebook':
                    picture_url = social.extra_data.get('picture', {}).get('data', {}).get('url')
                    if not picture_url:
                        picture_url = social.extra_data.get('picture')
                elif provider == 'github':
                    picture_url = social.extra_data.get('avatar_url')
                elif provider == 'twitter_oauth2':
                    # Twitter OAuth2 uses profile_image_url (may have _normal suffix)
                    picture_url = social.extra_data.get('profile_image_url')
                    # Remove _normal, _bigger, etc. to get original size
                    if picture_url:
                        picture_url = picture_url.replace('_normal', '').replace('_bigger', '').replace('_mini', '')
                elif provider == 'twitter':
                    # Legacy Twitter OAuth1.0a
                    picture_url = social.extra_data.get('profile_image_url_https')
                elif provider == 'apple':
                    picture_url = None

                if not picture_url:
                    self.stdout.write(self.style.WARNING(f'No picture URL found for {user.username} ({provider})'))
                    continue

                # Download the image
                try:
                    response = requests.get(picture_url, timeout=10)
                    response.raise_for_status()

                    # Get file extension
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
                        if '.jpg' in picture_url or '.jpeg' in picture_url:
                            ext = 'jpg'
                        elif '.png' in picture_url:
                            ext = 'png'
                        elif '.gif' in picture_url:
                            ext = 'gif'
                        else:
                            ext = 'jpg'

                    # Create filename and save (don't include directory, it's handled by upload_to)
                    filename = f"{user.username}_{uuid.uuid4().hex[:8]}.{ext}"
                    author.profile_picture.save(
                        filename,
                        ContentFile(response.content),
                        save=True
                    )

                    self.stdout.write(self.style.SUCCESS(f'✓ Updated profile picture for {user.username}'))
                    updated_count += 1

                except (requests.RequestException, IOError, OSError) as e:
                    self.stdout.write(self.style.ERROR(f'✗ Error downloading picture for {user.username}: {str(e)}'))
                    error_count += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Error processing {user.username}: {str(e)}'))
                error_count += 1

        self.stdout.write(self.style.SUCCESS(f'\nCompleted: {updated_count} updated, {error_count} errors'))

