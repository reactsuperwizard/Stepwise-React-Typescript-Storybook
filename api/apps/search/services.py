import logging

from haystack.query import SearchQuerySet

from apps.tenants.models import Tenant, User

logger = logging.getLogger(__name__)


def search(user: User, tenant: Tenant, query: str) -> SearchQuerySet:
    logger.info(f'User(id={user}) is searching for "{query}"')
    return SearchQuerySet().filter(tenant_id=tenant.pk).autocomplete(name_auto=query)
