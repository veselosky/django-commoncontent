"""
This settings file is used for testing Common Content when django.contrib.sites
is not installed.
"""

from importlib.util import find_spec
from pathlib import Path

import environ

import commoncontent.apps

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
VAR = BASE_DIR / "var"

# Get environment settings
env = environ.Env()
DOTENV = BASE_DIR / ".env"
if DOTENV.exists() and not env("IGNORE_ENV_FILE", default=False):
    environ.Env.read_env(DOTENV)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-ri51as9!afs^d0y_&%cf#jv)uud!dfky0k0ydioc_3u^va&5^+"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
SITE_ID = env("SITE_ID", cast=int, default=None)
LOGIN_REDIRECT_URL = "/"


# Application definition
INSTALLED_APPS = [
    # commoncontent apps for static site generation
    *commoncontent.apps.CONTENT,
    # commoncontent apps for publishing tools
    "django_extensions",
    "tinymce",
    # contrib apps required by commoncontent for statics
    "django.contrib.contenttypes",
    "django.contrib.humanize",
    # "django.contrib.redirects",
    "django.contrib.sitemaps",
    # "django.contrib.sites",
    "django.contrib.staticfiles",
    # contrib apps required by commoncontent for dynamically served apps
    "django.contrib.auth",
    "django.contrib.messages",
    "django.contrib.sessions",
    # Optional admin with commoncontent extensions
    "django.contrib.admin",
    "django.contrib.admindocs",
    "sitevars",
]

# Note: most of these middlewares are not required for static generation
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    # UpdateCacheMiddleware must be above LocaleMiddleware
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
MIDDLEWARE += [
    # "django.contrib.sites.middleware.CurrentSiteMiddleware",
    # "commoncontent.redirects.TemporaryRedirectFallbackMiddleware",
]
console = {"class": "logging.StreamHandler"}
if find_spec("rich"):
    console = {
        "class": "rich.logging.RichHandler",
        "formatter": "rich",
        "level": "DEBUG",
        "rich_tracebacks": True,
    }
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"rich": {"datefmt": "[%X]"}},
    "handlers": {"console": console},
    "loggers": {"": {"handlers": ["console"], "level": "DEBUG"}},
}

ROOT_URLCONF = "test_project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "commoncontent.apps.context_defaults",
                "sitevars.context_processors.inject_sitevars",
            ],
        },
    },
]

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

WSGI_APPLICATION = "test_project.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": VAR / "siteless.sqlite3",
    }
}

# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = "en-us"
TIME_ZONE = "America/New_York"
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images) and Media
# https://docs.djangoproject.com/en/4.0/howto/static-files/
STATICFILES_DIRS = [BASE_DIR / "test_project" / "static"]
STATIC_URL = "static/"
STATIC_ROOT = VAR / "static"
MEDIA_ROOT = VAR / "media"
MEDIA_URL = "media/"
if not STATIC_ROOT.exists():
    STATIC_ROOT.mkdir(parents=True, exist_ok=True)
if not MEDIA_ROOT.exists():
    MEDIA_ROOT.mkdir(parents=True, exist_ok=True)

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

TINYMCE_DEFAULT_CONFIG = commoncontent.apps.TINYMCE_CONFIG

#######################################################################
# DEVELOPMENT: If running in a dev environment, loosen restrictions
# and add debugging tools.
#######################################################################
if DEBUG:
    ALLOWED_HOSTS = ["*"]

    # Use the basic storage with no manifest
    STORAGES["staticfiles"]["BACKEND"] = (
        "django.contrib.staticfiles.storage.StaticFilesStorage"
    )
    if find_spec("debug_toolbar"):
        INSTALLED_APPS.append("debug_toolbar")
        MIDDLEWARE.append("debug_toolbar.middleware.DebugToolbarMiddleware")
        INTERNAL_IPS = [
            "127.0.0.1",
        ]
        # See also urls.py for debug_toolbar urls
