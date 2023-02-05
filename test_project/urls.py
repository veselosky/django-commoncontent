"""genericsite URL Configuration

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
from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from genericsite import views as generic


urlpatterns = [
    path("accounts/profile/", generic.ProfileView.as_view(), name="account_profile"),
    path("accounts/", include("allauth.urls")),
    path("django_accounts/", include("django.contrib.auth.urls")),
    path("admin/", admin.site.urls),
    path("tinymce/", include("tinymce.urls")),
    path("feed/", generic.SiteFeed(), name="site_feed"),
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
    # TODO Pagination URLs for sections and home page
]
if settings.DEBUG:
    # NOTE: When DEBUG and staticfiles is installed, Django automatically adds static
    # urls, but does not automatically serve MEDIA
    from django.conf.urls.static import static

    # Serve static and media files from development server
    # urlpatterns += staticfiles_urlpatterns()  # automatic when DEBUG on
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    try:
        import debug_toolbar

        # Wildcard patterns might match and block these if appended, hence insert
        urlpatterns.insert(0, path("__debug__/", include(debug_toolbar.urls)))
    except ImportError:
        pass
