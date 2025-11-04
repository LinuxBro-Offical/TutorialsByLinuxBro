# Linux Bro Blog

A Django-based blog platform with social authentication, nested comments, user profiles, and content management system.

## Features

- 📝 Blog posts with rich content blocks (text, images, YouTube videos)
- 🔐 Social authentication (Google, GitHub, Facebook, Apple, Twitter/X)
- 💬 Nested comments with replies (up to 3 levels) and likes
- 👤 User profiles and author profiles with follow functionality
- 🔖 Tag and category filtering
- 💾 Saved reads functionality
- 📊 Ad space management (AdSense, Meta Ads, Custom)
- 📧 Contact form with rate limiting
- 👥 Team member management

## Tech Stack

- **Backend**: Django 5.0.7
- **Authentication**: django-allauth
- **Database**: SQLite (development)
- **Environment**: python-decouple

## Prerequisites

- Python 3.10+
- pip
- Virtual environment (recommended)

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd linux_bro
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup environment variables**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and update:
   - `SECRET_KEY` - Generate a new Django secret key
   - `DEBUG` - Set to `False` in production
   - `ALLOWED_HOSTS` - Your domain(s), comma-separated
   - Social auth credentials (optional)

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Setup social authentication** (Optional)
   ```bash
   python manage.py create_social_apps
   ```
   Then update credentials in Django Admin → Social Applications → Social Applications

8. **Load sample data** (Optional)
   ```bash
   # If populate_sample_data.py exists in one_time_scripts/
   cp one_time_scripts/populate_sample_data.py home/management/commands/
   python manage.py populate_sample_data --clear
   ```

9. **Run server**
   ```bash
   python manage.py runserver
   ```

10. **Access**
    - Home: http://localhost:8000
    - Admin: http://localhost:8000/admin

## Project Structure

```
linux_bro/
├── home/              # Main app (models, views, templates)
├── accounts/          # User authentication
├── blog/              # Blog functionality
├── contact/           # Contact form
├── templates/v2/      # Frontend templates
├── static/            # Static files (CSS, JS, images)
├── media/             # Uploaded files
└── linux_bro/         # Project settings
```

## Environment Variables

Required in `.env`:
- `SECRET_KEY` - Django secret key
- `DEBUG` - Debug mode (True/False)
- `ALLOWED_HOSTS` - Comma-separated hosts
- `SITE_ID` - Site ID for allauth (default: 1)

Optional (Social Auth):
- `GOOGLE_CLIENT_ID`, `GOOGLE_SECRET`
- `GITHUB_CLIENT_ID`, `GITHUB_SECRET`
- `FACEBOOK_APP_ID`, `FACEBOOK_SECRET`
- `APPLE_CLIENT_ID`, `APPLE_SECRET`, `APPLE_KEY`
- `TWITTER_CONSUMER_KEY`, `TWITTER_CONSUMER_SECRET`

## Management Commands

- `create_social_apps` - Create placeholder social apps
- `cleanup_social_apps` - Remove duplicate social apps

## Key Models

- `Author` - User profiles with bio, profile picture, followers
- `Story` - Blog posts with cover images, categories, tags
- `ContentBlock` - Rich content (text, images, YouTube videos)
- `Response` - Nested comments/replies
- `CommentLike` - Comment likes
- `Saved` - Saved stories
- `AdSpace` - Ad unit management
- `TeamMember` - Team member profiles
- `ContactInfo`, `ContactMessage` - Contact form

## URLs

- `/` - Home page with blog listings
- `/blog/<uuid>` - Blog detail page
- `/profile/` - User profile
- `/author/<uuid>` - Author profile
- `/results/` - Filter/search results
- `/our-story/` - About Us page
- `/contact/` - Contact page
- `/admin/` - Django admin

## Notes

- SQLite database used for development
- Media files stored in `media/` directory
- Static files in `static/` directory
- `.env` file excluded from git (use `.env.example` as template)
- Social auth requires OAuth credentials from respective providers
