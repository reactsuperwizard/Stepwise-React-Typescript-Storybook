from celery_haystack.indexes import CelerySearchIndex
from haystack import indexes

from apps.core.dashboard import DashboardRoutes
from apps.wells.models import CustomWell, WellPlanner


class CustomWellRigIndex(CelerySearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, model_attr='name')
    tenant_id = indexes.IntegerField(model_attr='tenant_id', indexed=False)
    name = indexes.CharField(model_attr='name', indexed=False)
    type = indexes.CharField(default='Well', indexed=False)
    url = indexes.CharField(indexed=False)
    name_auto = indexes.EdgeNgramField(model_attr='name')

    def get_model(self):
        return CustomWell

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

    def prepare_url(self, obj: CustomWell) -> str:
        project = obj.project
        if project:
            return DashboardRoutes.projectWell.format(projectId=project.pk, wellId=obj.pk)
        return DashboardRoutes.well.format(wellId=obj.pk)


class WellPlannerIndex(CelerySearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, model_attr='name')
    tenant_id = indexes.IntegerField(model_attr='asset__tenant_id', indexed=False)
    name = indexes.CharField(model_attr='name__name', indexed=False)
    type = indexes.CharField(default='Well plan', indexed=False)
    url = indexes.CharField(indexed=False)
    name_auto = indexes.EdgeNgramField(model_attr='name')

    def get_model(self):
        return WellPlanner

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

    def prepare_url(self, obj: WellPlanner) -> str:
        return DashboardRoutes.updateWellPlan.format(wellPlanId=obj.pk)
