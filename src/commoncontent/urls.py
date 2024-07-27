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
from django.views.generic import RedirectView

from commoncontent import views as generic

urlpatterns = [
    path(
        "<slug:section_slug>/feed/", RedirectView.as_view(pattern_name="section_feed")
    ),
    path("feed/", RedirectView.as_view(pattern_name="site_feed")),
    # Home page pagination needs to come before the other page patterns to match.
    path("page_<int:page>.html", generic.HomePageView.as_view(), name="home_paginated"),
    path("author/", generic.AuthorListView.as_view(), name="author_list"),
    path(
        "author/<slug:author_slug>/index.rss", generic.AuthorFeed(), name="author_feed"
    ),
    path(
        "author/<slug:author_slug>/page_<int:page>.html",
        generic.AuthorView.as_view(),
        name="author_page_paginated",
    ),
    path(
        "author/<slug:author_slug>/", generic.AuthorView.as_view(), name="author_page"
    ),
    path(
        "<slug:section_slug>/page_<int:page>.html",
        generic.SectionView.as_view(),
        name="section_paginated",
    ),
    path(
        "<slug:section_slug>/<slug:series_slug>/<slug:article_slug>.html",
        generic.ArticleDetailView.as_view(),
        name="article_series_page",
    ),
    path(
        "<slug:section_slug>/<slug:series_slug>/",
        generic.ArticleSeriesView.as_view(),
        name="series_page",
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
    path("<slug:section_slug>/index.rss", generic.SectionFeed(), name="section_feed"),
    path("index.rss", generic.SiteFeed(), name="site_feed"),
    path("", generic.HomePageView.as_view(), name="home_page"),
]
