from celery_haystack.indexes import CelerySearchIndex
from haystack import indexes

from apps.core.dashboard import DashboardRoutes
from apps.emissions.models import Asset


class AssetIndex(CelerySearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, model_attr='name')
    tenant_id = indexes.IntegerField(model_attr='tenant_id', indexed=False)
    name = indexes.CharField(model_attr='name', indexed=False)
    type = indexes.CharField(default='Asset', indexed=False)
    url = indexes.CharField(indexed=False)
    name_auto = indexes.EdgeNgramField(model_attr='name')

    def get_model(self):
        return Asset

    def index_queryset(self, using=None):
        return self.get_model().objects.live()

    def update_object(self, instance, using=None):
        if instance.deleted:
            self.remove_object(instance, using)
        else:
            super().update_object(instance, using)

    def prepare_url(self, obj: Asset) -> str:
        return DashboardRoutes.updateAsset.format(assetId=obj.pk)
