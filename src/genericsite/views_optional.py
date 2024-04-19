import typing as T

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.views.generic import ListView, TemplateView

from genericsite.models import Image


######################################################################################
class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "registration/profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if "allauth" in settings.INSTALLED_APPS:  # use allauth views
            context["change_password_view"] = "account_change_password"
        else:  # use django.contrib.auth views
            context["change_password_view"] = "password_change"

        return context


######################################################################################
class TinyMCEImageListView(ListView):
    """This view provides an image list for the TinyMCE editor for easy insertion."""

    model = Image
    ordering = "-uploaded_dt"
    paginate_by = 25

    def render_to_response(
        self, context: T.Dict[str, T.Any], **response_kwargs: T.Any
    ) -> HttpResponse:
        images = context.get("page_obj")
        if images is None:
            images = context.get("object_list")

        def preset(i):
            if i.image_width < i.image_height:
                return "portrait_large"
            return "large"

        return JsonResponse(
            [
                {
                    "title": i.title,
                    # "value": get_thumbnailer(i.image_file)[preset(i)].url,
                }
                for i in images
            ],
            safe=False,
        )
