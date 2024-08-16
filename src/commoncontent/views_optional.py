import typing as T

from django.http import HttpResponse, JsonResponse
from django.views.generic import ListView

from commoncontent.models import Image


######################################################################################
class TinyMCEImageListView(ListView):
    """This view provides an image list for the TinyMCE editor for easy insertion."""

    model = Image
    ordering = "-upload_date"
    paginate_by = 25

    def render_to_response(
        self, context: T.Dict[str, T.Any], **response_kwargs: T.Any
    ) -> HttpResponse:
        images = context.get("page_obj")
        if images is None:
            images = context.get("object_list")

        return JsonResponse(
            [
                {
                    "title": i.title,
                    "value": i.portrait_large.url if i.is_portrait else i.large.url,
                }
                for i in images
            ],
            safe=False,
        )
