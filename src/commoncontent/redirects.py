from django.contrib.redirects.middleware import RedirectFallbackMiddleware
from django.http import HttpResponseRedirect


class TemporaryRedirectFallbackMiddleware(RedirectFallbackMiddleware):
    """Replaces contrib.redirects RedirectFallbackMiddleware to send response code 302
    (as recommended in the docs) rather than 301.
    """

    response_redirect_class = HttpResponseRedirect


class PermanentRedirectFallbackMiddleware(RedirectFallbackMiddleware):
    """For completeness, an empty subclass so users can always get their middleware
    from commoncontent.
    """

    pass
