from django.db import models
from django.contrib.auth.models import User
import uuid


class Author(models.Model):
    """
    Model representing an author of blog posts.
    """

    SEX_CHOICES = [
        ("M", "Male"),
        ("F", "Female"),
        ("O", "Other"),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, null=True)
    full_name = models.CharField(max_length=100, null=True, blank=True)
    sex = models.CharField(max_length=1, choices=SEX_CHOICES, null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    profile_picture = models.ImageField(
        upload_to="author_profiles/", null=True, blank=True
    )
    website = models.URLField(null=True, blank=True)
    twitter_handle = models.CharField(max_length=100, null=True, blank=True)
    linkedin_profile = models.URLField(null=True, blank=True)
    followers = models.ManyToManyField(
        "self", symmetrical=False, related_name="following", blank=True
    )
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username

    def follow(self, author):
        """
        Allows the current author to follow another author.

        Args:
            author (Author): The author to be followed.
        """
        if author != self:
            self.followers.add(author)

    def unfollow(self, author):
        """
        Allows the current author to unfollow another author.

        Args:
            author (Author): The author to be unfollowed.
        """
        self.followers.remove(author)

    def is_following(self, author):
        """
        Checks if the current author is following another author.

        Args:
            author (Author): The author to check.

        Returns:
            bool: True if the current author is following the specified author, False otherwise.
        """
        return self.following.filter(id=author.id).exists()

    def follower_count(self):
        """
        Returns the number of followers the current author has.

        Returns:
            int: The number of followers.
        """
        return self.followers.count()

    def following_count(self):
        """
        Returns the number of authors the current author is following.

        Returns:
            int: The number of authors being followed.
        """
        return self.following.count()

    def following_list(self):
        """
        Returns the number of authors the current author is following.

        Returns:
            int: The number of authors being followed.
        """
        return self.following.all()


class Category(models.Model):
    """
    Model representing a category under which blog posts can be grouped.

    Attributes:
        name (str): The name of the category.
        description (TextField, optional): A description of the category.
    """

    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name


class SubCategory(models.Model):
    """
    Model representing a sub-category under a specific category.

    Attributes:
        category (ForeignKey): A foreign key linking to the parent Category model.
        name (str): The name of the sub-category.
        description (TextField, optional): A description of the sub-category.
    """

    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="subcategories"
    )
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.category.name} - {self.name}"


class Tag(models.Model):
    """
    Model representing a tag that can be associated with a blog post.
    """

    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Convert the name to lowercase before saving
        self.name = self.name.lower()
        super().save(*args, **kwargs)


class Story(models.Model):
    """
    Model representing a blog post.
    """

    APPROVAL_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, null=True)
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=200, null=True, blank=True)
    cover_image = models.ImageField(upload_to="media/blog_images/", null=True, blank=True)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="stories")
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, related_name="blogs"
    )
    sub_category = models.ForeignKey(
        SubCategory, on_delete=models.SET_NULL, null=True, blank=True
    )
    tags = models.ManyToManyField(Tag, related_name="blogs")
    publication_date = models.DateTimeField(auto_now_add=True)
    approval_status = models.CharField(
        max_length=10, choices=APPROVAL_STATUS_CHOICES, default="pending"
    )
    # --- Banner fields ---
    is_banner = models.BooleanField(
        default=False,
        verbose_name="Display as Banner",
        help_text="Indicates whether this story should appear as a featured banner.",
    )
    # 1265 × 343 px
    banner_image = models.ImageField(
        upload_to="media/blog_banners/",
        null=True,
        blank=True,
        verbose_name="Banner Image",
        help_text="Optional banner image for featured display.",
    )
    # --- SEO fields ---
    meta_description = models.CharField(
        max_length=160,
        null=True,
        blank=True,
        verbose_name="Meta Description",
        help_text="SEO meta description (150-160 characters recommended). If left blank, will use subtitle or first content block.",
    )
    meta_keywords = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="Meta Keywords",
        help_text="Comma-separated keywords for SEO. If left blank, will use tags and category.",
    )

    def __str__(self):
        return self.title

    def is_saved_by_user(self, user):
        """
        Check if the given user has saved this story.

        Args:
            user (User): The user to check.

        Returns:
            bool: True if the story is saved by the user, otherwise False.
        """
        if not user.is_authenticated:
            return False
        return Saved.objects.filter(user=user.author, story=self).exists()

    def get_like_count(self):
        """
        Get the number of likes for this story.
        """
        return self.interactions.filter(liked=True).count()

    def get_comment_count(self):
        """
        Get the number of comments for this story.
        """
        return self.interactions.exclude(comment="").count()

    def is_liked_by_user(self, user):
        if not user:
            return False
        response = Response.objects.filter(author=user, story=self, comment=None).first()
        return response.liked if response else False


class StoryView(models.Model):
    """
    Model representing a user's view of a story.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="story_views")
    story = models.ForeignKey(
        Story, on_delete=models.CASCADE, related_name="story_views"
    )  # Updated related_name
    viewed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} viewed {self.story.title}"

    def total_views(self, story):
        """
        Returns the total number of views for a given story.

        Args:
            story (Story): The story for which to count views.

        Returns:
            int: The total number of views for the story.
        """
        return self.objects.filter(story=story).count()


class ContentBlock(models.Model):
    """
    Model representing a content block within a blog post.
    """

    CONTENT_TYPE_CHOICES = [
        ("paragraph", "Paragraph"),
        ("image", "Image"),
        ("blockquote", "Block Quote"),
        ("youtube", "YouTube Video"),
        ("code", "Code Block"),
    ]
    
    LANGUAGE_CHOICES = [
        ("", "Plain Text"),
        ("python", "Python"),
        ("javascript", "JavaScript"),
        ("java", "Java"),
        ("cpp", "C++"),
        ("c", "C"),
        ("html", "HTML"),
        ("css", "CSS"),
        ("sql", "SQL"),
        ("bash", "Bash/Shell"),
        ("json", "JSON"),
        ("xml", "XML"),
        ("yaml", "YAML"),
        ("markdown", "Markdown"),
        ("php", "PHP"),
        ("ruby", "Ruby"),
        ("go", "Go"),
        ("rust", "Rust"),
        ("swift", "Swift"),
        ("kotlin", "Kotlin"),
        ("typescript", "TypeScript"),
        ("dart", "Dart"),
    ]

    story = models.ForeignKey(
        Story, on_delete=models.CASCADE, related_name="content_blocks"
    )
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES)
    order = models.PositiveIntegerField()
    text_content = models.TextField(null=True, blank=True)
    image_content = models.ImageField(
        upload_to="media/blog_content_images/", null=True, blank=True
    )
    video_url = models.CharField(
        max_length=200, 
        null=True, 
        blank=True, 
        help_text="YouTube video ID (e.g., 'M06YHZ9YUdI') or full URL"
    )
    code_language = models.CharField(
        max_length=20,
        choices=LANGUAGE_CHOICES,
        default="",
        blank=True,
        help_text="Programming language for syntax highlighting (only used for code blocks)"
    )

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.story.title} - {self.content_type} (Order: {self.order})"
    
    def get_youtube_video_id(self):
        """Extract YouTube video ID from URL or return the ID if already extracted"""
        if not self.video_url:
            return None
        
        video_url = self.video_url.strip()
        
        # If it's already just an ID (11 characters, alphanumeric with - and _)
        if len(video_url) == 11 and all(c.isalnum() or c in '-_' for c in video_url):
            return video_url
        
        # Extract ID from various YouTube URL formats
        import re
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/watch\?.*[?&]v=([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/v\/([a-zA-Z0-9_-]{11})',
            r'youtu\.be\/([a-zA-Z0-9_-]{11})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, video_url)
            if match:
                video_id = match.group(1)
                # Validate it's 11 characters
                if len(video_id) == 11:
                    return video_id
        
        # If no pattern matches, check if it might be a valid ID anyway
        if len(video_url) == 11 and all(c.isalnum() or c in '-_' for c in video_url):
            return video_url
        
        # Return None if we can't extract a valid ID
        return None


class Response(models.Model):
    """
    Model representing user interactions with
    a blog post, such as likes and comments.
    """

    story = models.ForeignKey(
        Story, on_delete=models.CASCADE, related_name="interactions"
    )
    author = models.ForeignKey(
        Author, on_delete=models.CASCADE, related_name="interactions"
    )
    liked = models.BooleanField(default=False)
    comment = models.TextField(null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey(
        "self", null=True, blank=True, related_name="replies", on_delete=models.CASCADE
    )

    def __str__(self):
        return f"Interaction by {self.author.user.username} on {self.story.title}"

    reads = models.IntegerField(default=0)
    
    def get_like_count(self):
        """
        Get the number of likes for this comment.
        """
        return self.comment_likes.count()
    
    def is_liked_by_user(self, author):
        """
        Check if the comment is liked by the given author.
        
        Args:
            author (Author): The author to check.
            
        Returns:
            bool: True if the comment is liked by the author, otherwise False.
        """
        if not author:
            return False
        return self.comment_likes.filter(user=author).exists()
    
    @property
    def is_liked(self):
        """
        Property to check if comment is liked by current user.
        This is set dynamically in views before rendering.
        """
        if hasattr(self, '_is_liked'):
            return self._is_liked
        return False


class Saved(models.Model):
    """
    Model representing a saved blog post by a user, similar to Medium's save feature.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        Author, on_delete=models.CASCADE, related_name="saved_blogs"
    )
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name="saves")
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "story")
        ordering = ["-saved_at"]

    def __str__(self):
        return f"{self.user.username} saved {self.story.title}"

    @classmethod
    def get_saved_stories_by_user(self, user):
        """
        Retrieve all stories saved by the given user.

        Args:
            user (Author): The author for whom to retrieve saved stories.

        Returns:
            QuerySet: A queryset of Story objects saved by the user.
        """
        return (
            self.objects.filter(user=user).select_related("story").order_by("-saved_at")
        )

    def save_story(self, story, user):
        saved_instance, created = Saved.objects.get_or_create(story=story, user=user)
        return saved_instance, created


class CommentLike(models.Model):
    """
    Model representing a like on a comment.
    """
    
    comment = models.ForeignKey(
        Response, on_delete=models.CASCADE, related_name="comment_likes"
    )
    user = models.ForeignKey(
        Author, on_delete=models.CASCADE, related_name="comment_likes"
    )
    liked_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ("comment", "user")
        ordering = ["-liked_at"]
    
    def __str__(self):
        return f"{self.user.user.username} liked comment {self.comment.id}"


class TeamMember(models.Model):
    """
    Model representing a team member for the About Us page.
    """
    name = models.CharField(max_length=100)
    position = models.CharField(max_length=100)
    profile_picture = models.ImageField(
        upload_to="team_members/", null=True, blank=True
    )
    bio = models.TextField(null=True, blank=True)
    order = models.IntegerField(default=0, help_text="Order for display")
    is_active = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'created_date']
    
    def __str__(self):
        return f"{self.name} - {self.position}"


class ContactInfo(models.Model):
    """
    Model for storing contact information that can be edited from admin panel.
    Only one instance should exist.
    """
    company_name = models.CharField(max_length=200, default="Linux Bro")
    address_line1 = models.CharField(max_length=200, default="Empowering Tech Enthusiasts Worldwide")
    address_line2 = models.CharField(max_length=200, blank=True, null=True)
    phone1 = models.CharField(max_length=20, default="+1 234 567 890")
    phone2 = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(default="contact@linuxbro.com")
    map_latitude = models.CharField(max_length=20, default="48.8583701")
    map_longitude = models.CharField(max_length=20, default="2.2922873")
    map_zoom = models.IntegerField(default=17)
    
    class Meta:
        verbose_name = "Contact Information"
        verbose_name_plural = "Contact Information"
    
    def __str__(self):
        return f"Contact Info - {self.company_name}"
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if not self.pk:
            # If creating new instance, check if one already exists
            if ContactInfo.objects.exists():
                # Update existing instance instead
                existing = ContactInfo.objects.first()
                self.pk = existing.pk
                return super(ContactInfo, self).save(*args, **kwargs)
        super().save(*args, **kwargs)


class ContactMessage(models.Model):
    """
    Model for storing contact form messages.
    Used for rate limiting and message storage.
    """
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    ip_address = models.GenericIPAddressField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Message from {self.name} ({self.email})"
    
    @classmethod
    def get_message_count_today(cls, ip_address):
        """Get count of messages sent today from this IP"""
        from django.utils import timezone
        from datetime import timedelta
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        return cls.objects.filter(
            ip_address=ip_address,
            created_at__gte=today_start
        ).count()
    
    @classmethod
    def can_send_message(cls, ip_address, max_messages=2):
        """Check if IP can send more messages today"""
        return cls.get_message_count_today(ip_address) < max_messages


class AboutUsContent(models.Model):
    """Model for About Us page content sections"""
    
    # We're Creative Section
    creative_title = models.CharField(max_length=200, default="We're Creative")
    creative_lead = models.TextField(help_text="Lead paragraph for Creative section")
    creative_paragraph1 = models.TextField(help_text="First paragraph")
    creative_paragraph2 = models.TextField(help_text="Second paragraph")
    creative_paragraph3 = models.TextField(help_text="Third paragraph")
    creative_paragraph4 = models.TextField(help_text="Fourth paragraph")
    
    # We're Friendly Section
    friendly_title = models.CharField(max_length=200, default="We're Friendly")
    friendly_lead = models.TextField(help_text="Lead paragraph for Friendly section")
    friendly_paragraph1 = models.TextField(help_text="First paragraph")
    friendly_paragraph2 = models.TextField(help_text="Second paragraph")
    friendly_paragraph3 = models.TextField(help_text="Third paragraph")
    friendly_paragraph4 = models.TextField(help_text="Fourth paragraph")
    
    # Watch Our Video Section
    video_title_line1 = models.CharField(max_length=100, default="Watch our")
    video_title_line2 = models.CharField(max_length=100, default="video")
    video_description = models.TextField(help_text="Description text for video section")
    video_url = models.CharField(max_length=200, default="M06YHZ9YUdI", help_text="YouTube video ID")
    
    # Promote Your Company Section
    promote_title = models.CharField(max_length=200, default="Promote Your Company")
    promote_lead = models.CharField(max_length=200, default="Creating your own slogan here")
    promote_description = models.TextField(help_text="Description for Promote section")
    promote_button_text = models.CharField(max_length=100, default="Start Your Story")
    promote_button_link = models.CharField(max_length=200, default="/", help_text="Link URL for button")
    
    # Make a Project With Us Section
    project_title = models.CharField(max_length=200, default="Make a Project With Us")
    project_subtitle = models.CharField(max_length=200, default="Our Team is always ready to help you")
    project_description = models.TextField(help_text="Description for Project section")
    project_button_text = models.CharField(max_length=100, default="Get In Touch")
    project_button_link = models.CharField(max_length=200, default="/contact/", help_text="Link URL for button")
    
    # Meet The Team Section
    team_title = models.CharField(max_length=200, default="Meet The Team")
    team_subtitle = models.CharField(max_length=200, default="Meet the Linux Bro team")
    
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        """Ensure only one instance exists"""
        if not self.pk:
            # If creating new instance, check if one already exists
            if AboutUsContent.objects.exists():
                # Update existing instance instead
                existing = AboutUsContent.objects.first()
                self.pk = existing.pk
                return super(AboutUsContent, self).save(*args, **kwargs)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return "About Us Content"
    
    class Meta:
        verbose_name = "About Us Content"
        verbose_name_plural = "About Us Content"


class FooterContent(models.Model):
    """Model for Footer content across all pages"""
    
    mission_title = models.CharField(max_length=200, default="Our Mission")
    mission_text = models.TextField(help_text="Mission statement text")
    
    # Social Media Links
    facebook_url = models.URLField(blank=True, default="#")
    twitter_url = models.URLField(blank=True, default="#")
    linkedin_url = models.URLField(blank=True, default="#")
    github_url = models.URLField(blank=True, default="#")
    
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        """Ensure only one instance exists"""
        if not self.pk:
            # If creating new instance, check if one already exists
            if FooterContent.objects.exists():
                # Update existing instance instead
                existing = FooterContent.objects.first()
                self.pk = existing.pk
                return super(FooterContent, self).save(*args, **kwargs)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return "Footer Content"
    
    class Meta:
        verbose_name = "Footer Content"
        verbose_name_plural = "Footer Content"


class AdSpace(models.Model):
    """
    Model for managing ad spaces (AdSense, Meta Ads, etc.)
    """
    
    POSITION_CHOICES = [
        ('top', 'Top (Above Popular Posts)'),
        ('middle', 'Middle (Between Popular Posts and Tags)'),
        ('bottom', 'Bottom (Below Categories)'),
    ]
    
    AD_TYPE_CHOICES = [
        ('adsense', 'Google AdSense'),
        ('meta', 'Meta Ads (Facebook)'),
        ('custom', 'Custom HTML/JavaScript'),
    ]
    
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Internal name for this ad space (e.g., 'Sidebar Top Ad')"
    )
    position = models.CharField(
        max_length=20,
        choices=POSITION_CHOICES,
        help_text="Where this ad should appear in the sidebar"
    )
    ad_type = models.CharField(
        max_length=20,
        choices=AD_TYPE_CHOICES,
        default='adsense',
        help_text="Type of ad (AdSense, Meta Ads, or Custom)"
    )
    ad_code = models.TextField(
        help_text="Paste your AdSense code, Meta Ads code, or custom HTML/JavaScript here"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Only active ads will be displayed"
    )
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_position_display()})"
    
    class Meta:
        verbose_name = "Ad Space"
        verbose_name_plural = "Ad Spaces"
        ordering = ['position', 'name']
