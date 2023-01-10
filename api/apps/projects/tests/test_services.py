from copy import deepcopy
from unittest.mock import MagicMock

import pytest
from django.core.exceptions import ValidationError

from apps.emps.models import EMP
from apps.projects.factories import PlanFactory, PlanWellRelationFactory, ProjectFactory
from apps.projects.models import Plan, Project
from apps.projects.services import PlanData, create_plan, create_project, delete_project, update_plan, update_project
from apps.rigs.factories import CustomDrillshipFactory, CustomJackupRigFactory, CustomSemiRigFactory
from apps.rigs.models import CustomDrillship, CustomJackupRig, CustomSemiRig, RigType
from apps.studies.factories import StudyElementFactory
from apps.studies.models import StudyElement
from apps.tenants.factories import TenantFactory, UserFactory
from apps.wells.factories import CustomWellFactory
from apps.wells.models import CustomWell


@pytest.fixture
def project_data():
    return {
        "name": "Test project",
        "description": "Project description",
        "tugs_day_rate": 300.0,
        "tugs_avg_move_fuel_consumption": 33.3,
        "tugs_avg_transit_fuel_consumption": 12.3,
        "tugs_move_speed": 13.3,
        "tugs_transit_speed": 23.3,
        "ahv_no_used": 5,
        "ahv_no_days_per_location": 7,
        "ahv_avg_fuel_consumption": 3.0,
        "ahv_day_rate": 1000.0,
        "psv_calls_per_week": 2,
        "psv_types": "PS 213, PSV 153",
        "psv_day_rate": 7000.0,
        "psv_avg_fuel_transit_consumption": 123.45,
        "psv_avg_fuel_dp_consumption": 234.56,
        "psv_speed": 345.67,
        "psv_loading_time": 456.78,
        "psv_fuel_price": 2000.0,
        "helicopter_cruise_speed": 120.00,
        "helicopter_no_flights_per_week": 7,
        "helicopter_types": "UH-60 Black Hawk",
        "helicopter_avg_fuel_consumption": 3.5,
        "helicopter_rate_per_trip": 200.0,
        "helicopter_fuel_price": 333,
        "marine_diesel_oil_price": 3000,
        "co2_tax": 60,
        "nox_tax": 88,
        "fuel_total_price": 3456,
        "fuel_density": 66.6,
        "co2_emission_per_tonne_fuel": 3333.0,
        "co2_emission_per_m3_fuel": 4444.0,
    }


@pytest.mark.django_db
def test_create_project(project_data):
    tenant = TenantFactory()
    user = UserFactory()

    project = create_project(tenant=tenant, user=user, **project_data)

    assert project.tenant == tenant
    assert project.creator == user
    for field, value in project_data.items():
        assert getattr(project, field) == value


@pytest.mark.django_db
def test_update_project(project_data):
    project = ProjectFactory()
    user = UserFactory()
    project = update_project(project=project, user=user, **project_data)
    project = Project.objects.get(pk=project.pk)

    for field, value in project_data.items():
        assert getattr(project, field) == value


@pytest.mark.django_db
class TestCreatePlan:
    @pytest.fixture
    def project(self):
        return ProjectFactory()

    @pytest.fixture
    def rig(self, project):
        return CustomJackupRigFactory(project=project)

    @pytest.fixture
    def plan_data(self, project: Project, rig: CustomJackupRig) -> PlanData:
        well = CustomWellFactory(project=project)
        return {
            "name": "Plan name",
            "description": "Plan description",
            "block_name": "Plan block name",
            "reference_rig": {
                "type": RigType.JACKUP,
                "id": rig.pk,
            },
            "distance_from_tug_base_to_previous_well": 300,
            "wells": [
                {
                    "id": well.pk,
                    "distance_from_previous_location": 10,
                    "distance_to_helicopter_base": 20,
                    "distance_to_psv_base": 30,
                    "distance_to_ahv_base": 40,
                    "distance_to_tug_base": 50,
                    "jackup_positioning_time": 1.6,
                    "semi_positioning_time": 1.7,
                    "operational_time": 20,
                }
            ],
        }

    def test_should_create_plan(self, project: Project, rig: CustomJackupRig, plan_data: PlanData):
        user = UserFactory()

        plan = create_plan(user=user, project=project, **deepcopy(plan_data))

        assert plan.name == plan_data["name"]
        assert plan.description == plan_data["description"]
        assert plan.block_name == plan_data["block_name"]
        assert plan.reference_operation_jackup == rig
        assert plan.reference_operation_semi is None
        assert plan.reference_operation_drillship is None
        assert plan.distance_from_tug_base_to_previous_well == plan_data["distance_from_tug_base_to_previous_well"]
        assert plan.plan_wells.count() == 1

        plan_well = plan.plan_wells.get()
        well_data = plan_data["wells"][0]
        assert plan_well.well.pk == well_data["id"]
        assert plan_well.order == 0
        assert plan_well.distance_from_previous_location == well_data["distance_from_previous_location"]
        assert plan_well.distance_to_helicopter_base == well_data["distance_to_helicopter_base"]
        assert plan_well.distance_to_psv_base == well_data["distance_to_psv_base"]
        assert plan_well.distance_to_ahv_base == well_data["distance_to_ahv_base"]
        assert plan_well.distance_to_tug_base == well_data["distance_to_tug_base"]
        assert plan_well.jackup_positioning_time == well_data["jackup_positioning_time"]
        assert plan_well.semi_positioning_time == well_data["semi_positioning_time"]
        assert plan_well.operational_time == well_data["operational_time"]

    def test_should_raise_validation_error_for_invalid_well(self, project, plan_data: PlanData):
        user = UserFactory()
        well = CustomWellFactory()

        with pytest.raises(ValidationError, match=f"Well\\(pk={well.pk}\\) does not belong to the project."):
            create_plan(
                user=user,
                project=project,
                **{
                    **plan_data,
                    "wells": [
                        {
                            **plan_data["wells"][0],
                            "id": well.pk,
                        }
                    ],
                },
            )

    def test_should_raise_validation_error_for_unknown_reference_rig(self, project: Project, plan_data: PlanData):
        user = UserFactory()
        with pytest.raises(ValidationError, match="Invalid reference rig."):
            create_plan(
                user=user, project=project, **{**plan_data, "reference_rig": {"id": 1, "type": RigType.DRILLSHIP}}
            )

    def test_should_raise_validation_error_for_unsupported_reference_rig(self, project: Project, plan_data: PlanData):
        user = UserFactory()
        rig = CustomDrillshipFactory(project=project)
        with pytest.raises(ValidationError, match="Invalid reference rig."):
            create_plan(
                user=user, project=project, **{**plan_data, "reference_rig": {"id": rig.pk, "type": RigType.DRILLSHIP}}
            )

    def test_should_raise_validation_error_for_draft_project_well(self, project: Project, plan_data: PlanData):
        user = UserFactory()
        well = project.wells.get()
        well.draft = True
        well.save()

        with pytest.raises(ValidationError) as ex:
            create_plan(user=user, project=project, **plan_data)
        assert ex.value.messages == [f'Well(pk={well.pk}) does not belong to the project.']


@pytest.mark.django_db(transaction=True)
class TestUpdatePlan:
    @pytest.fixture
    def plan(self) -> Plan:
        return PlanFactory()

    @pytest.fixture
    def rig(self, plan: Plan) -> CustomSemiRig:
        return CustomSemiRigFactory(project=plan.project, dp=True)

    @pytest.fixture
    def plan_data(self, plan: Plan, rig: CustomSemiRig) -> PlanData:
        plan_well = PlanWellRelationFactory(plan=plan)
        PlanWellRelationFactory(plan=plan)
        well = CustomWellFactory()
        plan.project.wells.add(well)

        return {
            "name": "Updated plan name",
            "description": "Updated plan description",
            "block_name": "Updated plan block name",
            "reference_rig": {
                "id": rig.pk,
                "type": RigType.SEMI,
            },
            "distance_from_tug_base_to_previous_well": 500,
            "wells": [
                {
                    "id": plan_well.well.pk,
                    "distance_from_previous_location": 1,
                    "distance_to_helicopter_base": 2,
                    "distance_to_psv_base": 3,
                    "distance_to_ahv_base": 4,
                    "distance_to_tug_base": 50,
                    "jackup_positioning_time": 1.6,
                    "semi_positioning_time": 1.7,
                    "operational_time": 20,
                },
                {
                    "id": well.pk,
                    "distance_from_previous_location": 9,
                    "distance_to_helicopter_base": 10,
                    "distance_to_psv_base": 11,
                    "distance_to_ahv_base": 12,
                    "distance_to_tug_base": 13,
                    "jackup_positioning_time": 1.4,
                    "semi_positioning_time": 1.5,
                    "operational_time": 21,
                },
            ],
        }

    def test_should_update_plan(
        self,
        mock_sync_all_plan_co2_calculations_task: MagicMock,
        plan: Plan,
        rig: CustomSemiRig,
        plan_data: PlanData,
    ):
        user = UserFactory()
        updated_plan = update_plan(user=user, plan=plan, **deepcopy(plan_data))

        assert updated_plan.name == plan_data["name"]
        assert updated_plan.description == plan_data["description"]
        assert updated_plan.block_name == plan_data["block_name"]
        assert plan.reference_operation_jackup is None
        assert plan.reference_operation_semi == rig
        assert plan.reference_operation_drillship is None
        assert plan.distance_from_tug_base_to_previous_well == plan_data["distance_from_tug_base_to_previous_well"]

        plan_wells = updated_plan.plan_wells.order_by('order')
        wells_data = plan_data["wells"]
        assert plan_wells.count() == 2
        for index, plan_well in enumerate(plan_wells):
            assert plan_well.well.pk == wells_data[index]["id"]
            assert plan_well.order == index
            assert plan_well.distance_from_previous_location == wells_data[index]["distance_from_previous_location"]
            assert plan_well.distance_to_helicopter_base == wells_data[index]["distance_to_helicopter_base"]
            assert plan_well.distance_to_psv_base == wells_data[index]["distance_to_psv_base"]
            assert plan_well.distance_to_ahv_base == wells_data[index]["distance_to_ahv_base"]
            assert plan_well.distance_to_tug_base == wells_data[index]["distance_to_tug_base"]
            assert plan_well.jackup_positioning_time == wells_data[index]["jackup_positioning_time"]
            assert plan_well.semi_positioning_time == wells_data[index]["semi_positioning_time"]
            assert plan_well.operational_time == wells_data[index]["operational_time"]

        mock_sync_all_plan_co2_calculations_task.assert_called_once_with(plan.pk)

    def test_should_raise_value_error_for_invalid_well(
        self, mock_sync_all_plan_co2_calculations_task: MagicMock, plan: Plan, plan_data: PlanData
    ):
        user = UserFactory()
        well = CustomWellFactory()

        with pytest.raises(ValidationError, match=f"Well\\(pk={well.pk}\\) does not belong to the project."):
            update_plan(
                user=user,
                plan=plan,
                **{
                    **plan_data,
                    "wells": [
                        {
                            **plan_data["wells"][0],
                            "id": well.pk,
                        },
                        plan_data["wells"][1],
                    ],
                },
            )

        mock_sync_all_plan_co2_calculations_task.assert_not_called()

    def test_should_raise_validation_error_for_unknown_reference_rig(
        self, mock_sync_all_plan_co2_calculations_task: MagicMock, plan: Plan, plan_data: PlanData
    ):
        user = UserFactory()
        with pytest.raises(ValidationError, match="Invalid reference rig."):
            update_plan(user=user, plan=plan, **{**plan_data, "reference_rig": {"id": 1, "type": RigType.JACKUP}})

        mock_sync_all_plan_co2_calculations_task.assert_not_called()

    def test_should_raise_validation_error_for_unsupported_reference_rig(
        self, mock_sync_all_plan_co2_calculations_task: MagicMock, plan: Plan, plan_data: PlanData
    ):
        user = UserFactory()
        rig = CustomDrillshipFactory(project=plan.project)
        with pytest.raises(ValidationError, match="Invalid reference rig."):
            update_plan(
                user=user, plan=plan, **{**plan_data, "reference_rig": {"id": rig.pk, "type": RigType.DRILLSHIP}}
            )

        mock_sync_all_plan_co2_calculations_task.assert_not_called()

    def test_should_raise_value_error_for_new_draft_project_well(
        self, mock_sync_all_plan_co2_calculations_task: MagicMock, plan: Plan, plan_data: PlanData
    ):
        user = UserFactory()
        well = plan.project.wells.get()
        well.draft = True
        well.save()

        with pytest.raises(ValidationError) as ex:
            update_plan(user=user, plan=plan, **plan_data)

        assert ex.value.messages == [f'Well(pk={well.pk}) does not belong to the project.']
        mock_sync_all_plan_co2_calculations_task.assert_not_called()

    def test_should_raise_value_error_for_updated_draft_project_well(
        self, mock_sync_all_plan_co2_calculations_task: MagicMock, plan: Plan, plan_data: PlanData
    ):
        user = UserFactory()
        well = plan.wells.order_by('id').first()
        well.draft = True
        well.save()

        with pytest.raises(ValidationError) as ex:
            update_plan(user=user, plan=plan, **plan_data)

        assert ex.value.messages == [f'Well(pk={well.pk}) does not belong to the project.']
        mock_sync_all_plan_co2_calculations_task.assert_not_called()


@pytest.mark.django_db
def test_delete_project():
    user = UserFactory()
    tenant = TenantFactory()
    project = ProjectFactory(
        tenant=tenant,
    )
    semi_rig = CustomSemiRigFactory(tenant=tenant, emp=None, project=project)
    jackup_rig = CustomJackupRigFactory(tenant=tenant, project=project)
    drillship = CustomDrillshipFactory(tenant=tenant, project=project)
    emp = jackup_rig.emp
    well = CustomWellFactory(tenant=tenant, project=project)
    plan = PlanFactory(project=project)
    PlanWellRelationFactory(plan=plan, well=well)
    study_element = StudyElementFactory(project=project)

    delete_project(user=user, project=project)

    with pytest.raises(Project.DoesNotExist):
        project.refresh_from_db()
    with pytest.raises(CustomSemiRig.DoesNotExist):
        semi_rig.refresh_from_db()
    with pytest.raises(CustomJackupRig.DoesNotExist):
        jackup_rig.refresh_from_db()
    with pytest.raises(CustomDrillship.DoesNotExist):
        drillship.refresh_from_db()
    with pytest.raises(CustomWell.DoesNotExist):
        well.refresh_from_db()
    with pytest.raises(Plan.DoesNotExist):
        plan.refresh_from_db()
    with pytest.raises(EMP.DoesNotExist):
        emp.refresh_from_db()
    with pytest.raises(StudyElement.DoesNotExist):
        study_element.refresh_from_db()
