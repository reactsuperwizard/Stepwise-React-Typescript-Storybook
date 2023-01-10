from celery_haystack.indexes import CelerySearchIndex
from haystack import indexes

from apps.core.dashboard import DashboardRoutes
from apps.studies.models import Study


class StudyIndex(CelerySearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, model_attr='name')
    tenant_id = indexes.IntegerField(model_attr='tenant_id', indexed=False)
    name = indexes.CharField(model_attr='name', indexed=False)
    type = indexes.CharField(default='Benchmark', indexed=False)
    url = indexes.CharField(indexed=False)
    name_auto = indexes.EdgeNgramField(model_attr='name')

    def get_model(self):
        return Study

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

    def prepare_url(self, obj: Study) -> str:
        return DashboardRoutes.study.format(projectId=obj.pk)
