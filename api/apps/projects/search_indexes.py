from celery_haystack.indexes import CelerySearchIndex
from haystack import indexes

from apps.core.dashboard import DashboardRoutes
from apps.projects.models import Plan, Project


class ProjectIndex(CelerySearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, model_attr='name')
    tenant_id = indexes.IntegerField(model_attr='tenant_id', indexed=False)
    name = indexes.CharField(model_attr='name', indexed=False)
    type = indexes.CharField(default='Project', indexed=False)
    url = indexes.CharField(indexed=False)
    name_auto = indexes.EdgeNgramField(model_attr='name')

    def get_model(self):
        return Project

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

    def prepare_url(self, obj: Project) -> str:
        return DashboardRoutes.project.format(projectId=obj.pk)


class PlanIndex(CelerySearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, model_attr='name')
    tenant_id = indexes.IntegerField(model_attr='project__tenant_id', indexed=False)
    name = indexes.CharField(model_attr='name', indexed=False)
    type = indexes.CharField(default='Plan', indexed=False)
    url = indexes.CharField(indexed=False)
    name_auto = indexes.EdgeNgramField(model_attr='name')

    def get_model(self):
        return Plan

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

    def prepare_url(self, obj: Plan) -> str:
        return DashboardRoutes.updatePlan.format(projectId=obj.project_id, planId=obj.pk)
