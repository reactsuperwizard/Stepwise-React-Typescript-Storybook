import pytest
from haystack.query import SearchQuerySet

from apps.core.dashboard import DashboardRoutes
from apps.emissions.factories import AssetFactory
from apps.emissions.services import delete_asset
from apps.search.services import search
from apps.tenants.factories import TenantFactory, UserFactory


@pytest.mark.django_db(transaction=True)
def test_search_assets(clear_haystack):
    user = UserFactory()
    tenant = TenantFactory()

    active_asset = AssetFactory(tenant=tenant, name='Active asset')
    active_asset.save()
    deleted_asset = AssetFactory(name='Deleted asset', tenant=tenant)
    delete_asset(asset=deleted_asset, user=user)
    unknown_asset = AssetFactory(name='Unknown asset')
    unknown_asset.save()

    assert SearchQuerySet().count() == 2

    results = search(user=user, tenant=tenant, query='asset')

    assert results.count() == 1
    result = results[0]
    assert result.object == active_asset
    assert result.tenant_id == tenant.pk
    assert result.name == active_asset.name
    assert result.type == 'Asset'
    assert result.url == DashboardRoutes.updateAsset.format(assetId=active_asset.pk)
