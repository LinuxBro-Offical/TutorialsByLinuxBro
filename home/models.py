from django.db import models
from django.contrib.auth.models import User
import uuid


class Author(models.Model):
    """
    Model representing an author of blog posts.
    """
    SEX_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, null=True)
    full_name = models.CharField(max_length=100, null=True, blank=True)
    sex = models.CharField(max_length=1,
                           choices=SEX_CHOICES, null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to='author_profiles/',
                                        null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    twitter_handle = models.CharField(max_length=100, null=True, blank=True)
    linkedin_profile = models.URLField(null=True, blank=True)
    followers = models.ManyToManyField('self', symmetrical=False,
                                       related_name='following', blank=True)
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

    category = models.ForeignKey(Category,
                                 on_delete=models.CASCADE,
                                 related_name='subcategories')
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
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, null=True)
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=200, null=True, blank=True)
    cover_image = models.ImageField(upload_to='media/blog_images/')
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='stories')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL,
                                 null=True)
    sub_category = models.ForeignKey(SubCategory, on_delete=models.SET_NULL,
                                     null=True, blank=True)
    tags = models.ManyToManyField(Tag, related_name='blogs')
    publication_date = models.DateTimeField(auto_now_add=True)
    approval_status = models.CharField(max_length=10,
                                       choices=APPROVAL_STATUS_CHOICES,
                                       default='pending')

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
        return self.interactions.exclude(comment='').count()
    
    def is_liked_by_user(self, user):
        response = Response.objects.filter(author=user,
                                           story=self,
                                           liked=True)
        return True if len(response) == 1 else False

class StoryView(models.Model):
    """
    Model representing a user's view of a story.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='story_views')
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='story_views')  # Updated related_name
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
        ('paragraph', 'Paragraph'),
        ('image', 'Image'),
        ('blockquote', 'Block Quote'),
    ]

    story = models.ForeignKey(Story, on_delete=models.CASCADE,
                              related_name='content_blocks')
    content_type = models.CharField(max_length=20,
                                    choices=CONTENT_TYPE_CHOICES)
    order = models.PositiveIntegerField()
    text_content = models.TextField(null=True, blank=True)
    image_content = models.ImageField(upload_to='media/blog_content_images/',
                                      null=True, blank=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.story.title} - {self.content_type} (Order: {self.order})"


class Response(models.Model):
    """
    Model representing user interactions with
    a blog post, such as likes and comments.
    """

    story = models.ForeignKey(Story,
                              on_delete=models.CASCADE,
                              related_name='interactions')
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='interactions')
    liked = models.BooleanField(default=False)
    comment = models.TextField(null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='replies',
                               on_delete=models.CASCADE)

    def __str__(self):
        return f"Interaction by {self.author.user.username} on {self.story.title}"
    reads = models.IntegerField(default=0)


class Saved(models.Model):
    """
    Model representing a saved blog post by a user, similar to Medium's save feature.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='saved_blogs')
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='saves')
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'story')
        ordering = ['-saved_at']

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
        return self.objects.filter(user=user).select_related('story').order_by('-saved_at')


    def save_story(self, story, user):
        saved_instance, created = Saved.objects.get_or_create(story=story, user=user)
        return saved_instance, created
