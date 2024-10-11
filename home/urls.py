from django.urls import path
from .views import (LandingPageView, BlogPageView,
                    AboutUsView, AuthorProfileView,
                    MyProfileView, WalletView, RecentTransactions,
                    BlogListView, FollowAuthorView, SaveStoryView,
                    LikeStoryView, CommentAjaxView, DeleteCommentView,
                    FilterStoriesByTagView)

urlpatterns = [
    path('', LandingPageView.as_view(), name="home"),
    path('blog/<uuid:uuid>', BlogPageView.as_view(), name="blog"),
    path('our-story/', AboutUsView.as_view(), name="our_story"),
    path('author/<uuid:uuid>', AuthorProfileView.as_view(), name="author_profile"),
    path('profile/', MyProfileView.as_view(), name="my_profile"),
    path('wallet/', WalletView.as_view(), name="wallet"),
    path('transactions/', RecentTransactions.as_view(), name="transactions"),
    path('blogs/<slug:slug>/', BlogListView.as_view(), name='blog-list-slug'),
    path('follow-author/', FollowAuthorView.as_view(), name='follow-author'),
    path('save-story/', SaveStoryView.as_view(), name='save-story'),
    path('like/', LikeStoryView.as_view(), name='like_story'),
    path('comments/', CommentAjaxView.as_view(), name='comments_ajax'),
    path('delete/comment/', DeleteCommentView.as_view(), name='delete_comment'),
    path('filter-stories/', FilterStoriesByTagView.as_view(), name='filter_stories_by_tag'),
]
