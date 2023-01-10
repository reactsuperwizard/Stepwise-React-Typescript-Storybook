from django.conf import settings
from django.contrib.sites.models import Site


def get_domain_url() -> str:
    site = Site.objects.all().first()
    if not site:
        raise ValueError('Missing site')
    return site.domain


def get_app_url() -> str:
    return f"{settings.SERVER_PROTOCOL}://{get_domain_url()}"
