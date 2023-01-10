from celery_haystack.indexes import CelerySearchIndex
from haystack import indexes

from apps.core.dashboard import DashboardRoutes
from apps.monitors.models import Monitor


class MonitorIndex(CelerySearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, model_attr='name')
    tenant_id = indexes.IntegerField(model_attr='tenant_id', indexed=False)
    name = indexes.CharField(model_attr='name', indexed=False)
    type = indexes.CharField(default='Monitor', indexed=False)
    url = indexes.CharField(indexed=False)
    name_auto = indexes.EdgeNgramField(model_attr='name')

    def get_model(self):
        return Monitor

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(draft=False)

    def update_object(self, instance, using=None):
        if instance.draft:
            self.remove_object(instance, using)
        else:
            super().update_object(instance, using)

    def prepare_url(self, obj: Monitor) -> str:
        return DashboardRoutes.monitor.format(monitorId=obj.pk)
