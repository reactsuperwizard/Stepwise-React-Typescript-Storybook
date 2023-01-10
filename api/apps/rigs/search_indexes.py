from celery_haystack.indexes import CelerySearchIndex
from haystack import indexes

from apps.core.dashboard import DashboardRoutes, RigType
from apps.rigs.models import CustomDrillship, CustomJackupRig, CustomSemiRig


class CustomSemiRigIndex(CelerySearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, model_attr='name')
    tenant_id = indexes.IntegerField(model_attr='tenant_id', indexed=False)
    name = indexes.CharField(model_attr='name', indexed=False)
    type = indexes.CharField(default='Semi Rig', indexed=False)
    url = indexes.CharField(indexed=False)
    name_auto = indexes.EdgeNgramField(model_attr='name')

    def get_model(self):
        return CustomSemiRig

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

    def prepare_url(self, obj: CustomSemiRig) -> str:
        project = obj.project
        if project:
            return DashboardRoutes.projectRig.format(projectId=project.pk, rigType=RigType.Semi, rigId=obj.pk)
        return DashboardRoutes.rig.format(rigType=RigType.Semi, rigId=obj.pk)


class CustomJackupRigIndex(CelerySearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, model_attr='name')
    tenant_id = indexes.IntegerField(model_attr='tenant_id', indexed=False)
    name = indexes.CharField(model_attr='name', indexed=False)
    type = indexes.CharField(default='Jackup Rig', indexed=False)
    url = indexes.CharField(indexed=False)
    name_auto = indexes.EdgeNgramField(model_attr='name')

    def get_model(self):
        return CustomJackupRig

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

    def prepare_url(self, obj: CustomJackupRig) -> str:
        project = obj.project
        if project:
            return DashboardRoutes.projectRig.format(projectId=project.pk, rigType=RigType.Jackup, rigId=obj.pk)
        return DashboardRoutes.rig.format(rigType=RigType.Jackup, rigId=obj.pk)


class CustomDrillshipIndex(CelerySearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, model_attr='name')
    tenant_id = indexes.IntegerField(model_attr='tenant_id', indexed=False)
    name = indexes.CharField(model_attr='name', indexed=False)
    type = indexes.CharField(default='Drillship', indexed=False)
    url = indexes.CharField(indexed=False)
    name_auto = indexes.EdgeNgramField(model_attr='name')

    def get_model(self):
        return CustomDrillship

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

    def prepare_url(self, obj: CustomDrillship) -> str:
        project = obj.project
        if project:
            return DashboardRoutes.projectRig.format(projectId=project.pk, rigType=RigType.Drillship, rigId=obj.pk)
        return DashboardRoutes.rig.format(rigType=RigType.Drillship, rigId=obj.pk)
