from django.views.generic import TemplateView, DetailView
from .models import Story, Author


class LandingPageView(TemplateView):
    template_name = 'home/home_contents.html'

    def get_context_data(self, **kwargs):
        # Call the base implementation to get the default context
        context = super().get_context_data(**kwargs)
        # Add all stories to the context
        context['stories'] = Story.objects.all()
        return context


class BlogPageView(DetailView):
    model = Story
    template_name = 'home/blog.html'
    context_object_name = 'story'
    slug_field = 'uuid'
    slug_url_kwarg = 'uuid'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['content_blocks'] = self.object.content_blocks.all()
        context['like_count'] = self.object.interactions.filter(liked=True).count()
        context['comment_count'] = self.object.interactions.exclude(comment='').count()
        context['comments'] = self.object.interactions.exclude(comment='')
        return context


class AboutUsView(TemplateView):
    template_name = 'home/aboutus.html'


class MyProfileView(TemplateView):
    template_name = 'home/my_profile.html'


class AuthorProfileView(DetailView):
    model = Author
    template_name = 'home/author_profile.html'
    context_object_name = 'author'
    slug_field = 'uuid'
    slug_url_kwarg = 'uuid'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stories'] = self.object.stories.filter(approval_status='approved')
        context['like_count'] = self.object.interactions.filter(liked=True).count()
        context['comment_count'] = self.object.interactions.exclude(comment='').count()
        context['comments'] = self.object.interactions.exclude(comment='')
        return context



class WalletView(TemplateView):
    template_name = 'home/wallet.html'


class RecentTransactions(TemplateView):
    template_name = 'home/transactions.html'


class BlogListView(TemplateView):
    template_name = 'home/bloglist.html'
