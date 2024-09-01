from django.urls import path
from .views import (LandingPageView, BlogPageView,
                    AboutUsView, AuthorProfileView,
                    MyProfileView, WalletView, RecentTransactions,
                    BlogListView)

urlpatterns = [
    path('', LandingPageView.as_view(), name="home"),
    path('blog/<uuid:uuid>', BlogPageView.as_view(), name="blog"),
    path('our-story/', AboutUsView.as_view(), name="our_story"),
    path('author/<uuid:uuid>', AuthorProfileView.as_view(), name="author_profile"),
    path('profile/', MyProfileView.as_view(), name="my_profile"),
    path('wallet/', WalletView.as_view(), name="wallet"),
    path('transactions/', RecentTransactions.as_view(), name="transactions"),
    path('blog/list', BlogListView.as_view(), name="blog_list"),
]
