from django.http import HttpRequest
from django.shortcuts import render

TURBO_STREAM = "text/vnd.turbo-stream.html"


def is_turbo(request: HttpRequest) -> bool:
    return TURBO_STREAM in request.headers.get("Accept", "")


class TurboResponse:
    template_name_turbo = ""

    def render_to_response(self, context, **response_kwargs):
        r = super().render_to_response(context, **response_kwargs)
        if is_turbo(self.request):
            r["Content-Type"] = TURBO_STREAM
        return r

    def get_template_names(self) -> list[str]:
        if is_turbo(self.request):
            return [self.template_name_turbo]

        return super().get_template_names()


def render_turbo(*args, **kwargs):
    kwargs["content_type"] = TURBO_STREAM
    return render(*args, **kwargs)


class Form422Mixin:
    def form_invalid(self, form):
        resp = super().form_invalid(form)
        if resp.status_code == 200:
            resp.status_code = 422
        return resp
