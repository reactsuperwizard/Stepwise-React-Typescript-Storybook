from typing import Any

import factory
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory


class SessionRequestFactory(RequestFactory):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

        self.COOKIES: dict[str, str] = dict()
        self.META: dict[str, str] = dict()
        self.GET: dict[str, str] = dict()
        self.POST: dict[str, str] = dict()
        middleware = SessionMiddleware(self)  # type: ignore
        middleware.process_request(self)  # type: ignore
        self.session.save()  # type: ignore


class CleanDjangoModelFactory(factory.django.DjangoModelFactory):
    @classmethod
    def _after_postgeneration(cls, instance, create, results=None):
        if create and results:
            instance.full_clean()
        return super()._after_postgeneration(instance, create, results)
