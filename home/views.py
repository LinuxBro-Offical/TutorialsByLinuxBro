from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import HttpResponse, JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.views import View
from django.views.decorators.http import require_http_methods
from django.views.generic import DetailView, TemplateView

# Local application imports
from .forms import AuthorForm, TeamMemberForm
from .models import Author, Category, Response, Saved, Story, StoryView, Tag, CommentLike, TeamMember, ContactInfo, ContactMessage, AboutUsContent, FooterContent, AdSpace


def get_footer_content():
    """Helper function to get or create FooterContent"""
    footer_content = FooterContent.objects.first()
    if not footer_content:
        footer_content = FooterContent.objects.create()
    return footer_content


def get_user_author(user):
    """Helper function to get or create Author for a user"""
    if not user or not user.is_authenticated:
        return None
    try:
        return user.author
    except Author.DoesNotExist:
        # Create Author if it doesn't exist
        return Author.objects.create(
            user=user,
            full_name=user.get_full_name() or user.username
        )


class LandingPageView(TemplateView):
    """
    Renders the main blog landing page.

    Includes:
      - Paginated stories (latest first)
      - Popular stories
      - Tags and categories used in stories
      - Following authors (for logged-in users)
    """

    template_name = "v2/blog.html"

    def get_context_data(self, **kwargs):
        """Add paginated stories, tags, categories, and user-following data to context."""
        context = super().get_context_data(**kwargs)

        # Fetch all stories and apply ordering
        story_list = Story.objects.all().order_by("-publication_date")

        # --- Pagination setup ---
        paginator = Paginator(story_list, 3)
        page_number = self.request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        # Add paginated stories
        context["stories"] = page_obj
        context["page_obj"] = page_obj

        context["banner_stories"] = story_list.filter(is_banner=True)

        # Popular stories
        context["popular_stories"] = Story.objects.filter(
            approval_status="approved"
        ).order_by("-publication_date")[:5]

        # Tags and categories
        context["tags"] = Tag.objects.filter(blogs__isnull=False).distinct()[:8]
        context["categories"] = Category.objects.filter(blogs__isnull=False).distinct()[
            :8
        ]

        # Footer content
        context["footer_content"] = get_footer_content()
        
        # Fetch active ad spaces
        ad_spaces = {}
        active_ads = AdSpace.objects.filter(is_active=True)
        for ad in active_ads:
            if ad.position not in ad_spaces:
                ad_spaces[ad.position] = []
            ad_spaces[ad.position].append(ad)
        context["ad_spaces"] = ad_spaces
        
        # SEO context for homepage
        context['seo_title'] = 'Linux Bro - Tech Blog | Empowering Tech Enthusiasts'
        context['seo_description'] = 'Linux Bro - Empowering Tech Enthusiasts with tutorials, guides, and tech stories'

        return context


class BlogPageView(DetailView):
    model = Story
    template_name = "v2/blog_detail.html"
    context_object_name = "story"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Check if the user is authenticated before recording the view
        if self.request.user.is_authenticated:
            # Check if the user has already viewed this story
            if not StoryView.objects.filter(
                user=self.request.user, story=self.object
            ).exists():
                # Create a new StoryView record if the story hasn't been viewed by the user
                StoryView.objects.create(user=self.request.user, story=self.object)
            current_author = get_user_author(self.request.user)
            if current_author:
                context["is_following"] = self.object.author.followers.filter(
                    id=current_author.id
                ).exists()
                context["is_saved_story"] = self.object.is_saved_by_user(self.request.user)
                context["is_liked"] = self.object.is_liked_by_user(current_author)
            else:
                context["is_following"] = False
                context["is_saved_story"] = False
                context["is_liked"] = False
        else:
            # Optionally handle anonymous views (if needed)
            context["is_following"] = False
            context["is_liked"] = False
            context["is_saved_story"] = False
        # Popular stories
        context["popular_stories"] = Story.objects.filter(
            approval_status="approved"
        ).order_by("-publication_date")[:5]

        # Tags and categories
        context["tags"] = Tag.objects.filter(blogs__isnull=False).distinct()[:8]
        context["categories"] = Category.objects.filter(blogs__isnull=False).distinct()[
            :8
        ]
        context["content_blocks"] = self.object.content_blocks.all()
        context["like_count"] = self.object.interactions.filter(liked=True).count()
        context["comment_count"] = self.object.interactions.exclude(comment="").count()
        
        # Footer content
        context["footer_content"] = get_footer_content()
        
        # Fetch all comments including replies, prefetch replies for efficiency
        comments = self.object.interactions.exclude(comment="").prefetch_related('replies')
        all_comments_list = list(comments)
        
        # Get all reply IDs by traversing all comments and their replies recursively
        def get_all_reply_ids(comment_list):
            """Recursively collect all reply IDs"""
            reply_ids = []
            for comment in comment_list:
                for reply in comment.replies.all():
                    reply_ids.append(reply.id)
                    # Recursively get nested replies
                    nested_replies = get_all_reply_ids([reply])
                    reply_ids.extend(nested_replies)
            return reply_ids
        
        reply_ids = get_all_reply_ids(all_comments_list)
        
        # Pre-compute like status for ALL comments (including nested replies)
        if self.request.user.is_authenticated:
            user_author = get_user_author(self.request.user)
            if user_author:
                # Get all comment IDs including replies
                all_comment_ids = [c.id for c in all_comments_list]
                all_comment_ids.extend(reply_ids)
                all_comment_ids = list(set(all_comment_ids))
                
                liked_comment_ids = set(
                    CommentLike.objects.filter(comment_id__in=all_comment_ids, user=user_author)
                    .values_list('comment_id', flat=True)
                )
                
                # Create a dictionary of all comments for quick lookup
                comment_dict = {c.id: c for c in all_comments_list}
                # Also add replies to the dict
                all_replies = Response.objects.filter(id__in=reply_ids).select_related('author', 'parent')
                for reply in all_replies:
                    comment_dict[reply.id] = reply
                
                # Set _is_liked for all comments
                for comment_id, comment_obj in comment_dict.items():
                    comment_obj._is_liked = comment_id in liked_comment_ids
                
                # Critical: Set _is_liked on all prefetched replies (including nested ones)
                def set_like_on_replies(comment_obj):
                    """Recursively set like status on all replies"""
                    if hasattr(comment_obj, '_prefetched_objects_cache') and 'replies' in comment_obj._prefetched_objects_cache:
                        for reply in comment_obj._prefetched_objects_cache['replies']:
                            reply._is_liked = reply.id in liked_comment_ids
                            # Recursively set on nested replies
                            set_like_on_replies(reply)
                    else:
                        # If not prefetched, manually set it when accessing replies
                        for reply in comment_obj.replies.all():
                            reply._is_liked = reply.id in liked_comment_ids
                            set_like_on_replies(reply)
                
                for comment in all_comments_list:
                    set_like_on_replies(comment)
            else:
                # User authenticated but no author - set all to False
                def set_false_on_replies(comment_obj):
                    """Recursively set False on all replies"""
                    for reply in comment_obj.replies.all():
                        reply._is_liked = False
                        set_false_on_replies(reply)
                
                for comment in all_comments_list:
                    comment._is_liked = False
                    set_false_on_replies(comment)
        else:
            # Anonymous user - set all to False
            def set_false_on_replies(comment_obj):
                """Recursively set False on all replies"""
                for reply in comment_obj.replies.all():
                    reply._is_liked = False
                    set_false_on_replies(reply)
            
            for comment in all_comments_list:
                comment._is_liked = False
                set_false_on_replies(comment)
        
        context["comments"] = all_comments_list
        
        # Related posts based on tags (excluding current story)
        current_story_tags = self.object.tags.all()
        related_stories = Story.objects.filter(
            tags__in=current_story_tags,
            approval_status="approved"
        ).exclude(
            id=self.object.id
        ).distinct().annotate(
            view_count=Count("story_views"),
            comment_count=Count("interactions", filter=Q(interactions__comment__isnull=False) & ~Q(interactions__comment=""))
        ).order_by("-view_count", "-publication_date")[:3]
        
        context["related_stories"] = related_stories
        
        # Fetch active ad spaces
        ad_spaces = {}
        active_ads = AdSpace.objects.filter(is_active=True)
        for ad in active_ads:
            if ad.position not in ad_spaces:
                ad_spaces[ad.position] = []
            ad_spaces[ad.position].append(ad)
        context["ad_spaces"] = ad_spaces
        
        # SEO context
        context['seo_title'] = self.object.title
        context['seo_description'] = self.object.meta_description or self.object.subtitle or (self.object.content_blocks.first().text_content[:160] if self.object.content_blocks.exists() and self.object.content_blocks.first().text_content else "")
        context['seo_image'] = self.object.cover_image.url if self.object.cover_image else None
        
        return context


class AboutUsView(TemplateView):
    template_name = "v2/about_us.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Fetch active team members ordered by order field
        context["team_members"] = TeamMember.objects.filter(is_active=True).order_by('order', 'created_date')
        
        # Get About Us content (create default if doesn't exist)
        about_content = AboutUsContent.objects.first()
        if not about_content:
            about_content = AboutUsContent.objects.create()
        context["about_content"] = about_content
        
        # Get Footer content (create default if doesn't exist)
        footer_content = FooterContent.objects.first()
        if not footer_content:
            footer_content = FooterContent.objects.create()
        context["footer_content"] = footer_content
        
        # Latest approved stories for footer (most recent, not just popular)
        context["popular_stories"] = Story.objects.filter(
            approval_status="approved"
        ).order_by("-publication_date")[:5]
        return context


class ContactView(TemplateView):
    template_name = "v2/contact.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get contact info (create default if doesn't exist)
        contact_info = ContactInfo.objects.first()
        if not contact_info:
            contact_info = ContactInfo.objects.create()
        context["contact_info"] = contact_info
        
        # Footer content
        context["footer_content"] = get_footer_content()
        
        # Latest approved stories for footer (most recent, not just popular)
        context["popular_stories"] = Story.objects.filter(
            approval_status="approved"
        ).order_by("-publication_date")[:5]
        return context


class ContactFormView(View):
    """Handle contact form submission with rate limiting"""
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def post(self, request, *args, **kwargs):
        # Get client IP
        ip_address = self.get_client_ip(request)
        
        # Check rate limiting
        if not ContactMessage.can_send_message(ip_address, max_messages=2):
            message_count = ContactMessage.get_message_count_today(ip_address)
            return JsonResponse({
                'success': False,
                'error': 'rate_limit_exceeded',
                'message': f'You have already sent {message_count} messages today. Please try again tomorrow.',
                'message_count': message_count
            }, status=429)
        
        # Get form data
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        message = request.POST.get('message', '').strip()
        
        # Validate
        if not name or not email or not message:
            return JsonResponse({
                'success': False,
                'error': 'validation_error',
                'message': 'Please fill in all fields.'
            }, status=400)
        
        # Create contact message
        try:
            contact_message = ContactMessage.objects.create(
                name=name,
                email=email,
                message=message,
                ip_address=ip_address
            )
            
            # TODO: Send email notification here if needed
            # from django.core.mail import send_mail
            # send_mail(...)
            
            return JsonResponse({
                'success': True,
                'message': 'Thank you for your message! We will get back to you soon.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': 'server_error',
                'message': 'An error occurred. Please try again later.'
            }, status=500)


class TeamMemberListView(LoginRequiredMixin, View):
    """Get all team members for modal display"""
    def get(self, request, *args, **kwargs):
        team_members = TeamMember.objects.all().order_by('order', 'created_date')
        data = []
        for member in team_members:
            data.append({
                'id': member.id,
                'name': member.name,
                'position': member.position,
                'bio': member.bio or '',
                'profile_picture': member.profile_picture.url if member.profile_picture else '',
                'order': member.order,
                'is_active': member.is_active,
            })
        return JsonResponse({'team_members': data})


class TeamMemberCreateView(LoginRequiredMixin, View):
    """Create a new team member"""
    def post(self, request, *args, **kwargs):
        form = TeamMemberForm(request.POST, request.FILES)
        if form.is_valid():
            team_member = form.save()
            return JsonResponse({
                'success': True,
                'message': 'Team member created successfully.',
                'team_member': {
                    'id': team_member.id,
                    'name': team_member.name,
                    'position': team_member.position,
                    'bio': team_member.bio or '',
                    'profile_picture': team_member.profile_picture.url if team_member.profile_picture else '',
                    'order': team_member.order,
                    'is_active': team_member.is_active,
                }
            })
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)


class TeamMemberUpdateView(LoginRequiredMixin, View):
    """Update an existing team member"""
    def post(self, request, *args, **kwargs):
        team_member = get_object_or_404(TeamMember, id=request.POST.get('id'))
        form = TeamMemberForm(request.POST, request.FILES, instance=team_member)
        if form.is_valid():
            team_member = form.save()
            return JsonResponse({
                'success': True,
                'message': 'Team member updated successfully.',
                'team_member': {
                    'id': team_member.id,
                    'name': team_member.name,
                    'position': team_member.position,
                    'bio': team_member.bio or '',
                    'profile_picture': team_member.profile_picture.url if team_member.profile_picture else '',
                    'order': team_member.order,
                    'is_active': team_member.is_active,
                }
            })
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)


class TeamMemberDeleteView(LoginRequiredMixin, View):
    """Delete a team member"""
    def post(self, request, *args, **kwargs):
        team_member = get_object_or_404(TeamMember, id=request.POST.get('id'))
        team_member.delete()
        return JsonResponse({'success': True, 'message': 'Team member deleted successfully.'})


class MyProfileView(LoginRequiredMixin, TemplateView):
    template_name = "v2/my_profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get the current user
        user = self.request.user

        # Retrieve the Author object for the current user
        author = get_object_or_404(Author, user=user)

        # Add author details to context
        context["author"] = author
        saved_stories = Saved.objects.filter(user=author).select_related('story')
        
        # Liked stories - stories where user has liked=True in Response model
        liked_responses = Response.objects.filter(
            author=author, 
            liked=True,
            comment__isnull=True
        ).select_related('story').order_by('-date')
        liked_stories = [response.story for response in liked_responses]
        context["liked_stories"] = liked_stories

        # Retrieve stories published by the author - show all stories, not just 3
        stories = Story.objects.filter(author=author).order_by("-publication_date")
        context["stories"] = stories
        context["saved_stories"] = saved_stories
        
        # Get followed authors
        followed_authors = author.following.all()
        context["followed_authors"] = followed_authors
        context["followers"] = author.followers.all()

        # Popular stories for sidebar
        context["popular_stories"] = Story.objects.filter(
            approval_status="approved"
        ).order_by("-publication_date")[:5]

        # Tags and categories
        context["tags"] = Tag.objects.filter(blogs__isnull=False).distinct()[:8]
        context["categories"] = Category.objects.filter(blogs__isnull=False).distinct()[:8]

        # Footer content
        context["footer_content"] = get_footer_content()

        return context


class AuthorProfileView(DetailView):
    model = Author
    template_name = "v2/author_profile.html"
    context_object_name = "author"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get published stories
        published_stories = self.object.stories.filter(approval_status="approved").order_by("-publication_date")
        context["published_stories"] = published_stories
        
        # Get most liked stories (stories ordered by like count)
        most_liked_stories = Story.objects.filter(
            author=self.object,
            approval_status="approved"
        ).annotate(
            like_count=Count('interactions', filter=Q(interactions__liked=True))
        ).filter(like_count__gt=0).order_by('-like_count', '-publication_date')
        context["most_liked_stories"] = most_liked_stories
        
        # Get follower count
        context["followers_count"] = self.object.followers.count()
        context["following_count"] = self.object.following.count()
        
        # Check if current user is following this author
        if self.request.user.is_authenticated:
            current_author = get_user_author(self.request.user)
            if current_author:
                context["is_following"] = self.object.followers.filter(
                    id=current_author.id
                ).exists()
                # Check if viewing own profile
                context["is_own_profile"] = (current_author.id == self.object.id)
            else:
                context["is_following"] = False
                context["is_own_profile"] = False
        else:
            context["is_following"] = False
            context["is_own_profile"] = False
        
        # Sidebar content
        context["popular_stories"] = Story.objects.filter(
            approval_status="approved"
        ).order_by("-publication_date")[:5]
        
        context["tags"] = Tag.objects.filter(blogs__isnull=False).distinct()[:8]
        context["categories"] = Category.objects.filter(blogs__isnull=False).distinct()[:8]
        
        # Footer content
        context["footer_content"] = get_footer_content()
        
        return context


class FollowAuthorView(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        author_id = request.POST.get("author_id")
        author_to_follow = get_object_or_404(Author, id=author_id)
        current_author = get_user_author(request.user)
        
        if not current_author:
            return JsonResponse(
                {"error": "You must have an author profile to follow."}, status=403
            )

        if current_author in author_to_follow.followers.all():
            author_to_follow.unfollow(current_author)
            status = "unfollowed"
        else:
            author_to_follow.follow(current_author)
            status = "followed"

        return JsonResponse(
            {"status": status, "followers_count": author_to_follow.followers.count()}
        )

    def handle_no_permission(self):
        return JsonResponse(
            {"error": "You must be logged in to follow an author."}, status=403
        )


class SaveStoryView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        story_id = request.POST.get("story_id")
        story = get_object_or_404(Story, id=story_id)
        current_author = get_user_author(request.user)
        
        if not current_author:
            return JsonResponse(
                {"error": "You must have an author profile to save stories."}, status=403
            )

        # Check if the story is already saved
        saved_story, created = Saved.objects.get_or_create(
            user=current_author, story=story
        )

        if not created:
            # Story is already saved, so unsave it
            saved_story.delete()
            status = "unsaved"
        else:
            # Story was not saved, so save it
            status = "saved"

        return JsonResponse({"status": status})

    def handle_no_permission(self):
        return JsonResponse(
            {"error": "You must be logged in to save a story."}, status=403
        )


class LikeStoryView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        story_id = request.POST.get("story_id")
        story = Story.objects.get(id=story_id)
        current_author = get_user_author(request.user)
        
        if not current_author:
            return JsonResponse(
                {"error": "You must have an author profile to like stories."}, status=403
            )

        # Check if the user has already liked the story
        interaction, created = Response.objects.get_or_create(
            story=story, author=current_author, comment__isnull=True
        )
        
        if interaction.liked:
            interaction.liked = False
        else:
            interaction.liked = True

        interaction.save()

        # Return the updated like count
        like_count = story.get_like_count()
        return JsonResponse({"like_count": like_count, "liked": interaction.liked})


class CommentAjaxView(View):
    template_name = "v2/partials/comment_list.html"

    def get(self, *args, **kwargs):
        """Fetch all comments for a specific story"""
        context = dict()
        story_id = self.request.GET.get("story_id")
        story = get_object_or_404(Story, id=story_id)

        # Fetch all comments related to the story (excluding empty comments, ordered by date)
        # Prefetch replies to ensure they're loaded with the main queryset
        comments_qs = story.interactions.exclude(comment="").prefetch_related('replies').order_by('-date')
        all_comments_list = list(comments_qs)
        
        # Collect all reply IDs from prefetched replies
        reply_ids = []
        for comment in all_comments_list:
            if hasattr(comment, '_prefetched_objects_cache') and 'replies' in comment._prefetched_objects_cache:
                reply_ids.extend([r.id for r in comment._prefetched_objects_cache['replies']])
        
        # Get all comment IDs including replies
        all_comment_ids = [c.id for c in all_comments_list]
        all_comment_ids.extend(reply_ids)
        all_comment_ids = list(set(all_comment_ids))

        # Check if the user is authenticated before accessing author details
        if self.request.user.is_authenticated:
            user = get_user_author(self.request.user)
            if user:
                # Pre-compute like status for all comments (including nested replies)
                liked_comment_ids = set(
                    CommentLike.objects.filter(comment_id__in=all_comment_ids, user=user)
                    .values_list('comment_id', flat=True)
                )
            else:
                liked_comment_ids = set()
            
            # Set _is_liked for all top-level comments
            for comment in all_comments_list:
                comment._is_liked = comment.id in liked_comment_ids
            
            # Critical: Set _is_liked on all prefetched replies (including nested ones)
            def set_like_on_replies(comment_obj):
                """Recursively set like status on all replies"""
                if hasattr(comment_obj, '_prefetched_objects_cache') and 'replies' in comment_obj._prefetched_objects_cache:
                    for reply in comment_obj._prefetched_objects_cache['replies']:
                        reply._is_liked = reply.id in liked_comment_ids
                        # Recursively set on nested replies
                        set_like_on_replies(reply)
            
            for comment in all_comments_list:
                set_like_on_replies(comment)
        else:
            user = None
            for comment in all_comments_list:
                comment._is_liked = False
                # Set for replies too
                if hasattr(comment, '_prefetched_objects_cache') and 'replies' in comment._prefetched_objects_cache:
                    for reply in comment._prefetched_objects_cache['replies']:
                        reply._is_liked = False

        csrf_token = get_token(self.request) or None
        # Render the comments list into a partial template
        comments_html = render_to_string(
            self.template_name,
            {"comments": all_comments_list, "user": user, "csrf_token": csrf_token},
        )

        context["comments_html"] = comments_html
        return JsonResponse(context)

    def post(self, request, *args, **kwargs):
        """Add a new comment or reply to the specific story"""
        context = dict()
        
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Authentication required"}, status=403)
        
        story_id = request.POST.get("story_id")
        comment_text = request.POST.get("comment")
        parent_id = request.POST.get(
            "parent_id"
        )  # This will be None for top-level comments
        author = get_user_author(request.user)
        
        if not author:
            return JsonResponse(
                {"error": "You must have an author profile to comment."}, status=403
            )

        if comment_text and story_id:
            # Get the story the comment is associated with
            story = get_object_or_404(Story, id=story_id)

            # If a parent_id is provided, fetch the parent comment
            parent = None
            if parent_id:
                parent = get_object_or_404(Response, id=parent_id)

            # Create the new comment or reply
            new_response = Response.objects.create(
                story=story,
                author=author,
                comment=comment_text,
                parent=parent,  # Set the parent comment if it's a reply
            )

            csrf_token = get_token(self.request) or None
            user = get_user_author(self.request.user)
            
            # If it's a reply, return only the new reply HTML
            if parent_id:
                # Calculate the nesting level of the new reply
                level = 0
                current_parent = parent
                while current_parent:
                    level += 1
                    current_parent = current_parent.parent
                
                # Set like status for the new reply
                new_response._is_liked = False  # New comment can't be liked by creator
                
                # Render just the new reply
                reply_html = render_to_string(
                    "v2/partials/single_comment.html",
                    {
                        "comment": new_response,
                        "user": user,
                        "csrf_token": csrf_token,
                        "level": level,
                    },
                )
                context["reply_html"] = reply_html
                context["parent_id"] = parent_id
                context["is_reply"] = True
            else:
                # If it's a top-level comment, return the full list
                comments_qs = story.interactions.exclude(comment="").filter(parent=None).prefetch_related('replies').order_by('-date')
                all_comments_list = list(comments_qs)
                
                # Get all reply IDs by traversing recursively
                def get_all_reply_ids(comment_list):
                    """Recursively collect all reply IDs"""
                    reply_ids = []
                    for comment in comment_list:
                        if hasattr(comment, '_prefetched_objects_cache') and 'replies' in comment._prefetched_objects_cache:
                            for reply in comment._prefetched_objects_cache['replies']:
                                reply_ids.append(reply.id)
                                nested_replies = get_all_reply_ids([reply])
                                reply_ids.extend(nested_replies)
                        else:
                            for reply in comment.replies.all():
                                reply_ids.append(reply.id)
                                nested_replies = get_all_reply_ids([reply])
                                reply_ids.extend(nested_replies)
                    return reply_ids
                
                reply_ids = get_all_reply_ids(all_comments_list)
                
                # Get all comment IDs including replies
                all_comment_ids = [c.id for c in all_comments_list]
                all_comment_ids.extend(reply_ids)
                all_comment_ids = list(set(all_comment_ids))
                
                # Pre-compute like status for ALL comments (including nested replies)
                if user:
                    liked_comment_ids = set(
                        CommentLike.objects.filter(comment_id__in=all_comment_ids, user=user)
                        .values_list('comment_id', flat=True)
                    )
                    
                    # Set _is_liked for all top-level comments
                    for comment in all_comments_list:
                        comment._is_liked = comment.id in liked_comment_ids
                    
                    # Critical: Set _is_liked on all prefetched replies (including nested ones)
                    def set_like_on_replies(comment_obj):
                        """Recursively set like status on all replies"""
                        if hasattr(comment_obj, '_prefetched_objects_cache') and 'replies' in comment_obj._prefetched_objects_cache:
                            for reply in comment_obj._prefetched_objects_cache['replies']:
                                reply._is_liked = reply.id in liked_comment_ids
                                # Recursively set on nested replies
                                set_like_on_replies(reply)
                        else:
                            for reply in comment_obj.replies.all():
                                reply._is_liked = reply.id in liked_comment_ids
                                set_like_on_replies(reply)
                    
                    for comment in all_comments_list:
                        set_like_on_replies(comment)
                else:
                    def set_false_on_replies(comment_obj):
                        """Recursively set False on all replies"""
                        if hasattr(comment_obj, '_prefetched_objects_cache') and 'replies' in comment_obj._prefetched_objects_cache:
                            for reply in comment_obj._prefetched_objects_cache['replies']:
                                reply._is_liked = False
                                set_false_on_replies(reply)
                        else:
                            for reply in comment_obj.replies.all():
                                reply._is_liked = False
                                set_false_on_replies(reply)
                    
                    for comment in all_comments_list:
                        comment._is_liked = False
                        set_false_on_replies(comment)
                
                comments_html = render_to_string(
                    self.template_name,
                    {
                        "comments": all_comments_list,
                        "user": user,
                        "csrf_token": csrf_token,
                    },
                )
                context["comments_html"] = comments_html
                context["is_reply"] = False
            
            context["comment_count"] = story.interactions.exclude(comment="").count()

        return JsonResponse(context)


class DeleteCommentView(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        # Get the comment_id from the request body
        comment_id = request.POST.get("comment_id")
        comment = get_object_or_404(Response, id=comment_id)
        current_author = get_user_author(request.user)
        
        if not current_author:
            return JsonResponse(
                {"error": "You must have an author profile to delete comments."}, status=403
            )
        
        # Ensure the user deleting the comment is the author
        if comment.author == current_author:
            # Store the story object before deletion for fetching comments later
            story = comment.story
            comment.delete()

            # Fetch updated comments after deletion
            comments = story.interactions.exclude(comment="").filter(parent=None)

            csrf_token = get_token(self.request) or None

            # Render the updated comments list
            comments_html = render_to_string(
                "v2/partials/comment_list.html",
                {
                    "comments": comments,
                    "user": get_user_author(self.request.user),
                    "csrf_token": csrf_token,
                },
            )

            return JsonResponse(
                {
                    "status": "success",
                    "message": "Comment deleted successfully.",
                    "comments_html": comments_html,
                }
            )
        else:
            return JsonResponse(
                {
                    "status": "error",
                    "message": "You do not have permission to delete this comment.",
                },
                status=403,
            )


class LikeCommentView(LoginRequiredMixin, View):
    """View for liking/unliking a comment"""
    
    def post(self, request, *args, **kwargs):
        comment_id = request.POST.get("comment_id")
        comment = get_object_or_404(Response, id=comment_id)
        author = get_user_author(request.user)
        
        if not author:
            return JsonResponse(
                {"error": "You must have an author profile to like comments."}, status=403
            )
        
        # Get or create the like
        comment_like, created = CommentLike.objects.get_or_create(
            comment=comment,
            user=author
        )
        
        if not created:
            # If already exists, unlike it (delete)
            comment_like.delete()
            liked = False
        else:
            liked = True
        
        # Return updated like count
        like_count = comment.get_like_count()
        return JsonResponse({
            "liked": liked,
            "like_count": like_count
        })


class LoginView(View):
    def post(self, request, *args, **kwargs):
        mobile = request.POST.get("mobile")
        password = request.POST.get("password")

        # Assuming the User model uses mobile or email for login
        user = authenticate(request, username=mobile, password=password)

        if user is not None:
            login(request, user)
            return JsonResponse({"success": True})
        else:
            return JsonResponse(
                {"success": False, "error": "Invalid mobile number or password"}
            )


class CustomLogoutView(View):
    def get(self, request, *args, **kwargs):
        # Call the logout method to log the user out
        logout(request)
        # Redirect to the home page
        return redirect("home")


class AjaxSignupView(View):
    def post(self, request, *args, **kwargs):
        try:
            name = request.POST.get("name")
            mobile = request.POST.get("mobile")
            password = request.POST.get("password")
            cpassword = request.POST.get("cpassword")

            if password != cpassword:
                return JsonResponse(
                    {"success": False, "error": "Passwords do not match"}
                )

            if User.objects.filter(username=mobile).exists():
                return JsonResponse(
                    {"success": False, "error": "Mobile number already registered"}
                )

            # Create a new user
            user = User.objects.create(
                username=mobile, first_name=name, password=make_password(password)
            )
            auther = Author.objects.create(user=user, full_name=user.name)

            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})


class AuthorEditView(LoginRequiredMixin, View):
    """AJAX-only view for editing author profile"""
    model = Author
    form_class = AuthorForm

    def get_object(self):
        """Ensure the view edits only the current user's author profile"""
        return get_object_or_404(Author, user=self.request.user)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        # Check if this is an AJAX request
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if not is_ajax:
            return JsonResponse({"success": False, "error": "AJAX request required"}, status=400)
        
        # Handle standalone profile picture upload
        if 'profile_picture' in request.FILES and 'profile_picture' not in request.POST:
            try:
                self.object.profile_picture = request.FILES['profile_picture']
                self.object.save()
                return JsonResponse({
                    "success": True, 
                    "message": "Profile picture updated successfully.",
                    "profile_picture_url": self.object.profile_picture.url if self.object.profile_picture else None
                })
            except Exception as e:
                return JsonResponse({"success": False, "error": str(e)}, status=400)
        
        # Handle full form submission
        form = AuthorForm(request.POST, request.FILES, instance=self.object)
        if form.is_valid():
            form.save()
            return JsonResponse({"success": True, "message": "Author profile updated successfully."})
        else:
            return JsonResponse({"success": False, "errors": form.errors}, status=400)


class FilterSearchResultsView(TemplateView):
    """
    View for displaying filtered results by tag or search query.
    Same structure as home page but without carousel and blog images.
    """
    template_name = "v2/blog_results.html"

    def get_context_data(self, **kwargs):
        """Handle tag filtering and search queries."""
        context = super().get_context_data(**kwargs)
        
        # Initialize queryset with approved stories
        stories = Story.objects.filter(approval_status="approved").order_by("-publication_date")
        
        # Get tag from URL slug parameter
        tag_slug = self.kwargs.get("slug", None)
        
        # Get search query from GET parameter
        search_query = self.request.GET.get("q", "").strip()
        
        # Determine context title and filter stories
        if search_query:
            # Search filtering
            stories = stories.filter(
                Q(title__icontains=search_query)
                | Q(subtitle__icontains=search_query)
                | Q(tags__name__icontains=search_query)
                | Q(author__user__username__icontains=search_query)
            ).distinct()
            context["page_title"] = f"Search Results for: {search_query}"
            context["search_query"] = search_query
        elif tag_slug == "saved":
            # Handle saved reads
            if self.request.user.is_authenticated:
                current_author = get_user_author(self.request.user)
                if current_author:
                    saved_stories_ids = Saved.objects.filter(user=current_author).values_list(
                        "story_id", flat=True
                    )
                    stories = stories.filter(id__in=saved_stories_ids)
                    context["page_title"] = "Saved Reads"
                    context["tag_name"] = "saved"
                else:
                    stories = Story.objects.none()
                    context["page_title"] = "Saved Reads"
            else:
                stories = Story.objects.none()
                context["page_title"] = "Saved Reads"
        elif tag_slug:
            # Tag filtering
            try:
                tag = Tag.objects.get(
                    Q(name=tag_slug) | Q(name=tag_slug.lower()) | Q(name=tag_slug.upper())
                )
                stories = stories.filter(tags__name=tag.name).distinct()
                context["page_title"] = f"Stories tagged: {tag.name}"
                context["tag_name"] = tag.name
            except Tag.DoesNotExist:
                stories = Story.objects.none()
                context["page_title"] = "No Results Found"
        else:
            # Default: show all approved stories
            context["page_title"] = "All Stories"
        
        # Pagination
        paginator = Paginator(stories, 10)  # 10 stories per page
        page_number = self.request.GET.get("page")
        page_obj = paginator.get_page(page_number)
        
        context["stories"] = page_obj
        context["page_obj"] = page_obj
        
        # Popular stories for sidebar
        context["popular_stories"] = Story.objects.filter(
            approval_status="approved"
        ).order_by("-publication_date")[:5]
        
        # Tags and categories for sidebar
        context["tags"] = Tag.objects.filter(blogs__isnull=False).distinct()[:8]
        context["categories"] = Category.objects.filter(blogs__isnull=False).distinct()[:8]
        
        # Footer content
        context["footer_content"] = get_footer_content()
        
        return context


@require_http_methods(["GET"])
def robots_txt(request):
    """Generate robots.txt file"""
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
        "Disallow: /accounts/",
        "",
        f"Sitemap: {request.build_absolute_uri('/sitemap.xml')}",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")

