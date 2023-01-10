from celery_haystack.indexes import CelerySearchIndex
from haystack import indexes

from apps.core.dashboard import DashboardRoutes, RigType
from apps.emps.models import EMP
from apps.rigs.models import CustomDrillship, CustomJackupRig, CustomSemiRig


class EMPIndex(CelerySearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, model_attr='name')
    tenant_id = indexes.IntegerField(indexed=False)
    name = indexes.CharField(model_attr='name', indexed=False)
    type = indexes.CharField(default='EMP', indexed=False)
    url = indexes.CharField(indexed=False)
    name_auto = indexes.EdgeNgramField(model_attr='name')

    def get_model(self):
        return EMP

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

    def prepare_tenant_id(self, obj: EMP) -> int:
        try:
            return obj.customsemirig.tenant_id
        except CustomSemiRig.DoesNotExist:
            pass
        try:
            return obj.customjackuprig.tenant_id
        except CustomJackupRig.DoesNotExist:
            pass
        try:
            return obj.customdrillship.tenant_id
        except CustomDrillship.DoesNotExist:
            pass
        raise ValueError(f'EMP(id={obj.id}) is invalid. Missing rig.')

    def prepare_url(self, obj: EMP) -> str:
        try:
            rig = obj.customsemirig
            project = rig.project
            if not project:
                raise ValueError(f'EMP(id={obj.id}) is invalid. Missing project.')
            return DashboardRoutes.updateEMP.format(projectId=project.pk, rigType=RigType.Semi, rigId=rig.pk)
        except CustomSemiRig.DoesNotExist:
            pass
        try:
            rig = obj.customjackuprig
            project = rig.project
            if not project:
                raise ValueError(f'EMP(id={obj.id}) is invalid. Missing project.')
            return DashboardRoutes.updateEMP.format(projectId=project.pk, rigType=RigType.Jackup, rigId=rig.pk)
        except CustomJackupRig.DoesNotExist:
            pass
        try:
            rig = obj.customdrillship
            project = rig.project
            if not project:
                raise ValueError(f'EMP(id={obj.id}) is invalid. Missing project.')
            return DashboardRoutes.updateEMP.format(projectId=project.pk, rigType=RigType.Drillship, rigId=rig.pk)
        except CustomDrillship.DoesNotExist:
            pass
        raise ValueError(f'EMP(id={obj.id}) is invalid. Missing rig.')
