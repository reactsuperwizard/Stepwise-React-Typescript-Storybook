import pytest
from django.db import transaction

from apps.core.dashboard import DashboardRoutes, RigType
from apps.monitors.factories import MonitorFactory
from apps.projects.factories import PlanFactory, ProjectFactory
from apps.rigs.factories import CustomDrillshipFactory, CustomJackupRigFactory, CustomSemiRigFactory
from apps.search.services import search
from apps.tenants.factories import TenantFactory, UserFactory
from apps.wells.factories import CustomWellFactory, WellPlannerFactory


@pytest.mark.django_db(transaction=True)
class TestSearch:
    @pytest.fixture
    def user(self):
        return UserFactory()

    @pytest.fixture
    def tenant(self):
        return TenantFactory()

    def test_search_projects_and_studies(self, clear_haystack, user, tenant):
        project = ProjectFactory(tenant=tenant, name='Test project')
        ProjectFactory(name='Test project')

        results = sorted(search(user=user, tenant=tenant, query='project'), key=lambda result: result.type)

        assert len(results) == 2
        project_result = results[1]
        assert project_result.object == project
        assert project_result.tenant_id == tenant.pk
        assert project_result.name == project.name
        assert project_result.type == 'Project'
        assert project_result.url == DashboardRoutes.project.format(projectId=project.pk)
        project_result = results[0]
        assert project_result.object == project
        assert project_result.tenant_id == tenant.pk
        assert project_result.name == project.name
        assert project_result.type == 'Benchmark'
        assert project_result.url == DashboardRoutes.study.format(projectId=project.pk)

    def test_search_plans(self, clear_haystack, user, tenant):
        plan = PlanFactory(project__tenant=tenant, name='Test plan')
        PlanFactory(name='Test plan')

        results = search(user=user, tenant=tenant, query='plan')

        assert results.count() == 1
        result = results[0]
        assert result.object == plan
        assert result.tenant_id == tenant.pk
        assert result.name == plan.name
        assert result.type == 'Plan'
        assert result.url == DashboardRoutes.updatePlan.format(projectId=plan.project_id, planId=plan.pk)

    @pytest.mark.parametrize(
        'RigFactory, rig_type',
        (
            (CustomJackupRigFactory, RigType.Jackup),
            (CustomSemiRigFactory, RigType.Semi),
            (CustomDrillshipFactory, RigType.Drillship),
        ),
    )
    def test_search_emps(self, RigFactory, rig_type, clear_haystack, user, tenant):
        with transaction.atomic():
            project = ProjectFactory(tenant=tenant)
            rig = RigFactory(emp__name='Test Energy Management Plan', tenant=tenant, project=project)
            emp = rig.emp
            RigFactory(emp__name='Test Energy Management Plan')

        results = search(user=user, tenant=tenant, query='Management')

        assert results.count() == 1
        result = results[0]
        assert result.object == emp
        assert result.tenant_id == tenant.pk
        assert result.name == emp.name
        assert result.type == 'EMP'
        assert result.url == DashboardRoutes.updateEMP.format(projectId=project.pk, rigType=rig_type, rigId=rig.pk)

    def test_search_monitors(self, clear_haystack, user, tenant):
        monitor = MonitorFactory(tenant=tenant, name='Test monitor')
        MonitorFactory(tenant=tenant, draft=True)
        MonitorFactory(name='Test monitor')

        results = search(user=user, tenant=tenant, query='monitor')

        assert results.count() == 1
        result = results[0]
        assert result.object == monitor
        assert result.tenant_id == tenant.pk
        assert result.name == monitor.name
        assert result.type == 'Monitor'
        assert result.url == DashboardRoutes.monitor.format(monitorId=monitor.pk)

    @pytest.mark.parametrize(
        'RigFactory, rig_type, search_type',
        (
            (CustomJackupRigFactory, RigType.Jackup, 'Jackup Rig'),
            (CustomSemiRigFactory, RigType.Semi, 'Semi Rig'),
            (CustomDrillshipFactory, RigType.Drillship, 'Drillship'),
        ),
    )
    def test_search_project_rigs(self, RigFactory, rig_type, search_type, clear_haystack, user, tenant):
        with transaction.atomic():
            project = ProjectFactory(tenant=tenant)
            rig = RigFactory(name='Test Rig', project=project, tenant=tenant)
            RigFactory(name='Test Rig')

        results = search(user=user, tenant=tenant, query='rig')

        assert results.count() == 1
        result = results[0]
        assert result.object == rig
        assert result.tenant_id == tenant.pk
        assert result.name == rig.name
        assert result.type == search_type
        assert result.url == DashboardRoutes.projectRig.format(projectId=project.pk, rigType=rig_type, rigId=rig.pk)

    @pytest.mark.parametrize(
        'RigFactory, rig_type, search_type',
        (
            (CustomJackupRigFactory, RigType.Jackup, 'Jackup Rig'),
            (CustomSemiRigFactory, RigType.Semi, 'Semi Rig'),
            (CustomDrillshipFactory, RigType.Drillship, 'Drillship'),
        ),
    )
    def test_search_rigs(self, RigFactory, rig_type, search_type, clear_haystack, user, tenant):
        rig = RigFactory(name='Test Rig', tenant=tenant, project=None)
        RigFactory(name='Test Rig', project=None)

        results = search(user=user, tenant=tenant, query='Rig')

        assert results.count() == 1
        result = results[0]
        assert result.object == rig
        assert result.tenant_id == tenant.pk
        assert result.name == rig.name
        assert result.type == search_type
        assert result.url == DashboardRoutes.rig.format(rigType=rig_type, rigId=rig.pk)

    def test_search_wells(self, clear_haystack, user, tenant):
        well = CustomWellFactory(tenant=tenant, name='Test well', project=None)
        CustomWellFactory(name='Test well', project=None)

        results = search(user=user, tenant=tenant, query='well')

        assert results.count() == 1
        result = results[0]
        assert result.object == well
        assert result.tenant_id == tenant.pk
        assert result.name == well.name
        assert result.type == 'Well'
        assert result.url == DashboardRoutes.well.format(wellId=well.pk)

    def test_search_project_wells(self, clear_haystack, user, tenant):
        with transaction.atomic():
            project = ProjectFactory(tenant=tenant)
            well = CustomWellFactory(tenant=tenant, name='Test well', project=project)
            CustomWellFactory(name='Test well', project=ProjectFactory())

        results = search(user=user, tenant=tenant, query='well')

        assert results.count() == 1
        result = results[0]
        assert result.object == well
        assert result.tenant_id == tenant.pk
        assert result.name == well.name
        assert result.type == 'Well'
        assert result.url == DashboardRoutes.projectWell.format(wellId=well.pk, projectId=project.pk)

    def test_search_well_plans(self, clear_haystack, user, tenant):
        well_plan = WellPlannerFactory(asset__tenant=tenant, name__name='Test Well Plan')
        WellPlannerFactory(name__name='Unknown Well Plan')

        results = search(user=user, tenant=tenant, query='well')

        assert results.count() == 1
        result = results[0]
        assert result.object == well_plan
        assert result.tenant_id == tenant.pk
        assert result.name == well_plan.name.name
        assert result.type == 'Well plan'
        assert result.url == DashboardRoutes.updateWellPlan.format(wellPlanId=well_plan.pk)
