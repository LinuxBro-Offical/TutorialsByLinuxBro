from django.views.generic import TemplateView, DetailView, UpdateView
from .models import Story, Author, Saved, Response, StoryView, Tag
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.db.models import Count
from django.template.loader import render_to_string
from braces.views import JSONResponseMixin
from django.middleware.csrf import get_token
from django.core.paginator import Paginator
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from .forms import AuthorForm

class LandingPageView(TemplateView):
    template_name = 'home/home_contents.html'

    def get_context_data(self, **kwargs):
        # Call the base implementation to get the default context
        context = super().get_context_data(**kwargs)
        
        # Get the authors that the current user is following
        if hasattr(self.request.user, 'author'):
            following_authors = self.request.user.author.following_list()
        else:
            following_authors = []

        # Print the following authors for debugging
        print(following_authors)

        # Add all stories to the context
        context['foryou_stories'] = Story.objects.all().order_by("-publication_date")
        
        # Add stories from the followed authors to the context
        context["following_stories"] = Story.objects.filter(author__in=following_authors).order_by("-publication_date")

        context['trending_stories'] = Story.objects.annotate(
                                            view_count=Count('story_views')
                                        ).order_by('-view_count')[:5]
        
        current_user = self.request.user  if self.request.user.is_authenticated else None
        context["viewed_stories"] = Story.objects.filter(
                                        story_views__user=current_user
                                    ).order_by('-story_views__viewed_at').distinct()[:3]
        return context


class BlogPageView(DetailView):
    model = Story
    template_name = 'home/blog.html'
    context_object_name = 'story'
    slug_field = 'uuid'
    slug_url_kwarg = 'uuid'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Check if the user is authenticated before recording the view
        if self.request.user.is_authenticated:
            # Check if the user has already viewed this story
            if not StoryView.objects.filter(user=self.request.user, story=self.object).exists():
                # Create a new StoryView record if the story hasn't been viewed by the user
                StoryView.objects.create(user=self.request.user, story=self.object)
            current_author = self.request.user.author
            context["is_following"] = self.object.author.followers.filter(id=current_author.id).exists()
            context['is_saved_story'] = self.object.is_saved_by_user(self.request.user)
            context['is_liked'] = self.object.is_liked_by_user(current_author)
        else:
            # Optionally handle anonymous views (if needed)
            context["is_following"] = False
            context['is_liked'] = False
            context['is_saved_story'] = False
        context['content_blocks'] = self.object.content_blocks.all()
        context['like_count'] = self.object.interactions.filter(liked=True).count()
        context['comment_count'] = self.object.interactions.exclude(comment='').count()
        context['comments'] = self.object.interactions.exclude(comment='')
        return context


class AboutUsView(TemplateView):
    template_name = 'home/aboutus.html'


class MyProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'home/my_profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get the current user
        user = self.request.user

        # Retrieve the Author object for the current user
        author = get_object_or_404(Author, user=user)

        # Add author details to context
        context['author'] = author
        saved_stories = Saved.objects.filter(user=author)[:3]

        # Retrieve stories published by the author
        stories = Story.objects.filter(author=author).order_by('-publication_date')[:3]
        context['stories'] = stories
        context['saved_stories'] = saved_stories
        context['followers'] = author.followers.all()

        return context


class AuthorProfileView(DetailView):
    model = Author
    template_name = 'home/author_profile.html'
    context_object_name = 'author'
    slug_field = 'uuid'
    slug_url_kwarg = 'uuid'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stories'] = self.object.stories.filter(approval_status='approved')
        if self.request.user.is_authenticated:
            current_author = self.request.user.author
            context["is_following"] = self.object.followers.filter(id=current_author.id).exists()

            # Check if each story is saved by the current user
            saved_stories = Saved.objects.filter(user=current_author, story__in=context['stories'])
            saved_story_ids = saved_stories.values_list('story_id', flat=True)
            context['saved_story_ids'] = saved_story_ids
        else:
            context["is_following"] = False
        return context



class WalletView(TemplateView):
    template_name = 'home/wallet.html'


class RecentTransactions(TemplateView):
    template_name = 'home/transactions.html'



class BlogListView(TemplateView):
    template_name = 'home/bloglist.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slug = self.kwargs.get('slug', None)
        print(slug)
        current_author = self.request.user.author if self.request.user.is_authenticated else None

        # Initialize the base queryset
        stories = Story.objects.filter(approval_status='approved')

        if self.request.GET.get('search'):
            # Apply search filtering
            search_query = self.request.GET.get('search')
            stories = stories.filter(
                Q(title__icontains=search_query) | 
                Q(subtitle__icontains=search_query) |
                Q(tags__name__icontains=search_query) |
                Q(author__name__icontains=search_query)
            ).distinct()

        if slug == "saved" and current_author:
            # Filter to show only stories saved by the current user
            saved_stories_ids = Saved.objects.filter(user=current_author).values_list('story_id', flat=True)
            stories = stories.filter(id__in=saved_stories_ids)
            context["title"] = "Saved Reads"
            context["slug"] = slug
        else:
            try:
                title = Tag.objects.get(Q(name=slug) | Q(name=slug.lower()) | Q(name=slug.upper()))
                context["title"] = title.name
                stories = Story.objects.filter(tags__name=slug)
            except Exception:
                context["title"] = slug.lower()
                stories = {}

        # Add final queryset to context
        context['stories'] = stories
        context['tags'] = Tag.objects.all()

        # Check if each story is saved by the current user
        saved_stories = Saved.objects.filter(user=current_author, story__in=context['stories'])
        saved_story_ids = saved_stories.values_list('story_id', flat=True)
        context['saved_story_ids'] = saved_story_ids

        # Add saved status for each story if the user is authenticated
        if current_author:
            saved_story_ids = Saved.objects.filter(user=current_author, story__in=stories).values_list('story_id', flat=True)
            context['saved_story_ids'] = saved_story_ids
        else:
            context['saved_story_ids'] = []

        return context


class FollowAuthorView(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        author_id = request.POST.get('author_id')
        author_to_follow = get_object_or_404(Author, id=author_id)
        current_author = request.user.author

        if current_author in author_to_follow.followers.all():
            author_to_follow.unfollow(current_author)
            status = 'unfollowed'
        else:
            author_to_follow.follow(current_author)
            status = 'followed'

        return JsonResponse({
            'status': status,
            'followers_count': author_to_follow.followers.count()
        })

    def handle_no_permission(self):
        return JsonResponse({'error': 'You must be logged in to follow an author.'}, status=403)


class SaveStoryView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        story_id = request.POST.get('story_id')
        story = get_object_or_404(Story, id=story_id)
        current_author = request.user.author

        # Check if the story is already saved
        saved_story, created = Saved.objects.get_or_create(user=current_author, story=story)

        if not created:
            # Story is already saved, so unsave it
            saved_story.delete()
            status = 'unsaved'
        else:
            # Story was not saved, so save it
            status = 'saved'

        return JsonResponse({
            'status': status
        })

    def handle_no_permission(self):
        return JsonResponse({'error': 'You must be logged in to save a story.'}, status=403)


class LikeStoryView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        story_id = request.POST.get('story_id')
        story = Story.objects.get(id=story_id)
        
        # Check if the user has already liked the story
        interaction, created = Response.objects.get_or_create(story=story,
                                                              author=request.user.author,
                                                              comment__isnull=True)
        
        if interaction.liked:
            interaction.liked = False
        else:
            interaction.liked = True
            
        interaction.save()

        # Return the updated like count
        like_count = story.get_like_count()
        return JsonResponse({'like_count': like_count, 'liked': interaction.liked})


class CommentAjaxView(View, JSONResponseMixin):
    template_name = 'home/comment_list.html'

    def get(self, *args, **kwargs):
        """Fetch all comments for a specific story"""
        context = dict()
        story_id = self.request.GET.get('story_id')
        story = get_object_or_404(Story, id=story_id)

        # Fetch all comments related to the story (excluding empty comments)
        comments = story.interactions.exclude(comment='')

        # Check if the user is authenticated before accessing author details
        if self.request.user.is_authenticated:
            user = self.request.user.author
        else:
            user = None

        csrf_token = get_token(self.request) or None
        # Render the comments list into a partial template
        comments_html = render_to_string(self.template_name, {
            'comments': comments,
            'user': user,
            'csrf_token': csrf_token
        })
        
        context['comments_html'] = comments_html
        return self.render_json_response(context)

    def post(self, request, *args, **kwargs):
        """Add a new comment or reply to the specific story"""
        context = dict()
        story_id = request.POST.get('story_id')
        comment_text = request.POST.get('comment')
        parent_id = request.POST.get('parent_id')  # This will be None for top-level comments
        author = request.user.author  # Assuming the user has an 'author' profile

        print("parent:", parent_id)
        if comment_text and story_id:
            # Get the story the comment is associated with
            story = get_object_or_404(Story, id=story_id)

            # If a parent_id is provided, fetch the parent comment
            parent = None
            if parent_id:
                parent = get_object_or_404(Response, id=parent_id)

            # Create the new comment or reply
            Response.objects.create(
                story=story,
                author=author,
                comment=comment_text,
                parent=parent  # Set the parent comment if it's a reply
            )

            # Fetch updated comments after adding the new one
            comments = story.interactions.exclude(comment='').filter(parent=None)
            csrf_token = get_token(self.request) or None
            # Render the updated comments list
            comments_html = render_to_string(self.template_name, {
                'comments': comments,
                'user': self.request.user.author or None,
                'csrf_token': csrf_token
            })
            context['comments_html'] = comments_html

        return self.render_json_response(context)


class DeleteCommentView(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        # Get the comment_id from the request body
        comment_id = request.POST.get('comment_id')
        comment = get_object_or_404(Response, id=comment_id)
        print()
        # Ensure the user deleting the comment is the author
        if comment.author == request.user.author:
            # Store the story object before deletion for fetching comments later
            story = comment.story
            comment.delete()

            # Fetch updated comments after deletion
            comments = story.interactions.exclude(comment='').filter(parent=None)

            csrf_token = get_token(self.request) or None

            # Render the updated comments list
            comments_html = render_to_string('home/comment_list.html', {
                'comments': comments,
                'user': self.request.user.author or None,
                'csrf_token': csrf_token
            })

            return JsonResponse({
                'status': 'success',
                'message': 'Comment deleted successfully.',
                'comments_html': comments_html
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'You do not have permission to delete this comment.'
            }, status=403)


class FilterStoriesByTagView(View):
    def get(self, request, *args, **kwargs):
        # Get selected tags from the AJAX request
        tags = request.GET.getlist('tags[]')  # 'tags[]' because it's a multi-select

        # Filter the stories based on selected tags
        stories = Story.objects.filter(tags__name__in=tags).distinct()

        # Render the blog list as HTML
        blog_html = render_to_string('home/blog_filter.html', {
            'stories': stories,
        })

        # Send the rendered HTML back to the frontend
        return JsonResponse({'blog_html': blog_html})


class LoadMoreBlogsView(View):
    def get(self, request, *args, **kwargs):
        page = int(request.GET.get('page', 1))

        print("Page recieved", page)
        
        author = get_object_or_404(Author, user=self.request.user)

        stories = Story.objects.filter(
                    author=author).order_by('-publication_date')
        
        # Use Django's Paginator to paginate stories (3 per page)
        paginator = Paginator(stories, 3)

        try:
            stories_page = paginator.page(page)
        except Exception:
            return JsonResponse({'has_more_stories': False})
        
        # Render the new stories to a string using a template
        html = render_to_string('home/blog_published.html',
                                {'stories': stories_page})

        return JsonResponse({
            'html': html,
            'has_more_stories': stories_page.has_next()
        })


class LoginView(View):
    def post(self, request, *args, **kwargs):
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        
        # Assuming the User model uses mobile or email for login
        user = authenticate(request, username=mobile, password=password)
        
        if user is not None:
            login(request, user)
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Invalid mobile number or password'})


class CustomLogoutView(View):
    def get(self, request, *args, **kwargs):
        # Call the logout method to log the user out
        logout(request)
        # Redirect to the home page
        return redirect('home') 


class AjaxSignupView(View):
    def post(self, request, *args, **kwargs):
        try:
            name = request.POST.get('name')
            mobile = request.POST.get('mobile')
            password = request.POST.get('password')
            cpassword = request.POST.get('cpassword')

            if password != cpassword:
                return JsonResponse({'success': False, 'error': 'Passwords do not match'})
            
            if User.objects.filter(username=mobile).exists():
                return JsonResponse({'success': False, 'error': 'Mobile number already registered'})
            
            # Create a new user
            user = User.objects.create(
                username=mobile,
                first_name=name,
                password=make_password(password)
            )
            auther = Author.objects.create(
                user=user,
                full_name=user.name
            )

            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})


class AuthorEditView(LoginRequiredMixin, UpdateView):
    model = Author
    form_class = AuthorForm
    template_name = 'home/profile_update.html'

    def get_object(self):
        # Ensure the view edits only the current user's author profile
        return get_object_or_404(Author, user=self.request.user)

    def form_valid(self, form):
        # Handle AJAX form submission
        if self.request.is_ajax():
            form.save()
            data = {
                'message': 'Author profile updated successfully.'
            }
            return JsonResponse(data)
        return super().form_valid(form)

    def form_invalid(self, form):
        if self.request.is_ajax():
            return JsonResponse({'errors': form.errors}, status=400)
        return super().form_invalid(form)