from django.http import HttpRequest, HttpResponse


def sentry_debug(request: HttpRequest) -> HttpResponse:
    raise Exception("Sentry test exception")
