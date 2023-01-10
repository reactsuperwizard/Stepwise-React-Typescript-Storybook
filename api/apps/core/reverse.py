from typing import cast

from django.conf import settings
from furl import furl

from apps.tenants.models import Tenant


def dashboard_reverse(*, tenant: Tenant, page: str, **params: str) -> str:
    f = furl(f'{settings.SERVER_PROTOCOL}://{tenant.subdomain}')
    if settings.DASHBOARD_PORT:
        f.port = settings.DASHBOARD_PORT
    return cast(str, f.add(path=page.format(**params)).url)
