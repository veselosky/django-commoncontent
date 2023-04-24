"""URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path

from genericsite import views as generic

urlpatterns = [
    path("accounts/profile/", generic.ProfileView.as_view(), name="account_profile"),
    path("feed/", generic.SiteFeed(), name="site_feed"),
    path(
        "images/recent.json",
        generic.TinyMCEImageListView.as_view(),
        name="tinymce_image_list",
    ),
    path(
        "<slug:section_slug>/<slug:article_slug>.html",
        generic.ArticleDetailView.as_view(),
        name="article_page",
    ),
    path(
        "<slug:page_slug>.html", generic.PageDetailView.as_view(), name="landing_page"
    ),
    path("<slug:section_slug>/", generic.SectionView.as_view(), name="section_page"),
    path("<slug:section_slug>/feed/", generic.SectionFeed(), name="section_feed"),
    path("", generic.HomePageView.as_view(), name="home_page"),
]
