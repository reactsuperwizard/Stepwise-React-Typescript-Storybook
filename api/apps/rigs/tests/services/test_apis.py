import logging
from unittest.mock import MagicMock

import pytest
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from pytest_mock import MockerFixture

from apps.projects.factories import PlanFactory, PlanWellRelationFactory, ProjectFactory
from apps.rigs.factories import (
    CustomDrillshipFactory,
    CustomJackupPlanCO2Factory,
    CustomJackupRigFactory,
    CustomJackupSubareaScoreFactory,
    CustomSemiPlanCO2Factory,
    CustomSemiRigFactory,
    CustomSemiSubareaScoreFactory,
)
from apps.rigs.models import (
    CustomDrillship,
    CustomJackupPlanCO2,
    CustomJackupRig,
    CustomJackupSubareaScore,
    CustomSemiPlanCO2,
    CustomSemiRig,
    CustomSemiSubareaScore,
)
from apps.rigs.services.apis import (
    create_custom_drillship,
    create_custom_jackup_rig,
    create_custom_semi_rig,
    delete_custom_rig,
    sync_custom_jackup_plan_co2,
    sync_custom_jackup_subarea_score,
    sync_custom_semi_plan_co2,
    sync_custom_semi_subarea_score,
    update_custom_drillship,
    update_custom_jackup_rig,
    update_custom_semi_rig,
)
from apps.rigs.services.co2calculator.jackup import JackupCO2PerWellResult
from apps.rigs.services.co2calculator.semi import SemiCO2PerWellResult
from apps.rigs.tests.fixtures import (
    CUSTOM_DRILLSHIP_SERIALIZED_DRAFT_DATA,
    CUSTOM_DRILLSHIP_SERIALIZED_PUBLIC_DATA,
    CUSTOM_JACKUP_RIG_SERIALIZED_DRAFT_DATA,
    CUSTOM_JACKUP_RIG_SERIALIZED_PUBLIC_DATA,
    CUSTOM_SEMI_RIG_SERIALIZED_DRAFT_DATA,
    CUSTOM_SEMI_RIG_SERIALIZED_PUBLIC_DATA,
)
from apps.studies.factories import StudyElementSemiRigRelationFactory
from apps.studies.models import StudyElementSemiRigRelation
from apps.tenants.factories import TenantFactory, UserFactory

logger = logging.getLogger(__name__)


@pytest.fixture
def expected_concept_cj70_subarea_scores() -> dict:
    return dict(
        rig_status=1,
        topside_efficiency=1,
        deck_efficiency=1,
        move_and_installation=1,
        capacities=1,
        co2=1,
    )


@pytest.fixture
def expected_concept_cs60_subarea_scores() -> dict:
    return dict(
        rig_status=1.0,
        topside_efficiency=1.0,
        deck_efficiency=1.0,
        wow=1.0,
        capacities=1.0,
        co2=1.0,
    )


@pytest.mark.django_db
class TestCreateCustomSemiRig:
    @pytest.mark.parametrize('data', (CUSTOM_SEMI_RIG_SERIALIZED_PUBLIC_DATA, CUSTOM_SEMI_RIG_SERIALIZED_DRAFT_DATA))
    def test_create_rig(self, data):
        tenant = TenantFactory()
        user = UserFactory()

        rig = create_custom_semi_rig(tenant=tenant, user=user, **data)

        assert rig.tenant == tenant
        assert rig.creator == user

        for field, value in data.items():
            assert getattr(rig, field) == value

    def test_assign_rig_to_project(self):
        tenant = TenantFactory()
        user = UserFactory()
        project = ProjectFactory(tenant=tenant)

        rig = create_custom_semi_rig(
            tenant=tenant, user=user, project=project.pk, **CUSTOM_SEMI_RIG_SERIALIZED_PUBLIC_DATA
        )

        assert rig.project == project

    def test_validate_project(self):
        tenant = TenantFactory()
        user = UserFactory()
        project = ProjectFactory()

        with pytest.raises(ValidationError) as ex:
            create_custom_semi_rig(
                tenant=tenant, user=user, project=project.pk, **CUSTOM_SEMI_RIG_SERIALIZED_PUBLIC_DATA
            )

        assert ex.value.message_dict == {'project': [f'Project {project.pk} doesn\'t exist']}


@pytest.mark.django_db
class TestUpdateCustomSemiRig:
    @pytest.fixture
    def mock_sync_custom_semi_subarea_score_task(self, mocker: MockerFixture) -> MagicMock:
        mock_sync_custom_semi_subarea_score_task = mocker.patch(
            "apps.rigs.tasks.sync_custom_semi_subarea_score_task.delay"
        )
        return mock_sync_custom_semi_subarea_score_task

    @pytest.mark.parametrize(
        'data, draft', ((CUSTOM_SEMI_RIG_SERIALIZED_PUBLIC_DATA, False), (CUSTOM_SEMI_RIG_SERIALIZED_DRAFT_DATA, True))
    )
    def test_update_custom_semi_rig(self, data: dict, draft: bool, mock_sync_custom_semi_subarea_score_task: MagicMock):
        rig = CustomSemiRigFactory(draft=draft)
        user = UserFactory()

        rig = update_custom_semi_rig(rig=rig, user=user, **data)
        rig = CustomSemiRig.objects.get(pk=rig.pk)

        for field, value in data.items():
            assert getattr(rig, field) == value

        if draft:
            mock_sync_custom_semi_subarea_score_task.assert_not_called()
        else:
            mock_sync_custom_semi_subarea_score_task.assert_called_once_with(rig.pk)

    def test_cannot_mark_public_semi_rig_as_draft(self):
        rig = CustomSemiRigFactory(draft=False)
        user = UserFactory()

        with pytest.raises(ValidationError) as ex:
            update_custom_semi_rig(rig=rig, user=user, **CUSTOM_SEMI_RIG_SERIALIZED_DRAFT_DATA)
        assert ex.value.message_dict == {'draft': ['Public rig cannot be marked as draft.']}

    def test_remove_study_elements_for_not_studiable_rigs(self):
        rig = CustomSemiRigFactory()
        StudyElementSemiRigRelationFactory(rig=rig)
        user = UserFactory()

        assert StudyElementSemiRigRelation.objects.filter(rig=rig).count() == 1

        update_custom_semi_rig(
            rig=rig, user=user, **{**CUSTOM_SEMI_RIG_SERIALIZED_PUBLIC_DATA, "dp": False, "thruster_assist": False}
        )

        assert StudyElementSemiRigRelation.objects.filter(rig=rig).count() == 0


@pytest.mark.django_db
class TestCreateCustomJackupRig:
    @pytest.mark.parametrize(
        'data', (CUSTOM_JACKUP_RIG_SERIALIZED_PUBLIC_DATA, CUSTOM_JACKUP_RIG_SERIALIZED_DRAFT_DATA)
    )
    def test_create_custom_jackup_rig(self, data):
        tenant = TenantFactory()
        user = UserFactory()

        rig = create_custom_jackup_rig(tenant=tenant, user=user, **data)

        assert rig.tenant == tenant
        assert rig.creator == user

        for field, value in data.items():
            assert getattr(rig, field) == value

    def test_assign_rig_to_project(self):
        tenant = TenantFactory()
        user = UserFactory()
        project = ProjectFactory(tenant=tenant)

        rig = create_custom_jackup_rig(
            tenant=tenant, user=user, project=project.pk, **CUSTOM_JACKUP_RIG_SERIALIZED_PUBLIC_DATA
        )

        assert rig.project == project

    def test_validate_project(self):
        tenant = TenantFactory()
        user = UserFactory()
        project = ProjectFactory()

        with pytest.raises(ValidationError) as ex:
            create_custom_jackup_rig(
                tenant=tenant, user=user, project=project.pk, **CUSTOM_JACKUP_RIG_SERIALIZED_PUBLIC_DATA
            )

        assert ex.value.message_dict == {'project': [f'Project {project.pk} doesn\'t exist']}


@pytest.mark.django_db
class TestUpdateCustomJackupRig:
    @pytest.fixture
    def mock_sync_custom_jackup_subarea_score_task(self, mocker: MockerFixture) -> MagicMock:
        mock_sync_custom_jackup_subarea_score_task = mocker.patch(
            "apps.rigs.tasks.sync_custom_jackup_subarea_score_task.delay"
        )
        return mock_sync_custom_jackup_subarea_score_task

    @pytest.mark.parametrize(
        'data, draft',
        ((CUSTOM_JACKUP_RIG_SERIALIZED_PUBLIC_DATA, False), (CUSTOM_JACKUP_RIG_SERIALIZED_DRAFT_DATA, True)),
    )
    def test_update_custom_jackup_rig(
        self, mock_sync_custom_jackup_subarea_score_task: MagicMock, data: dict, draft: bool
    ):
        rig = CustomJackupRigFactory(draft=draft)
        user = UserFactory()

        rig = update_custom_jackup_rig(rig=rig, user=user, **data)
        rig = CustomJackupRig.objects.get(pk=rig.pk)

        for field, value in data.items():
            assert getattr(rig, field) == value

        assert mock_sync_custom_jackup_subarea_score_task.called is not draft
        if not draft:
            mock_sync_custom_jackup_subarea_score_task.assert_called_once_with(rig.pk)

    def test_cannot_mark_public_jackup_rig_as_draft(self, mock_sync_custom_jackup_subarea_score_task: MagicMock):
        rig = CustomJackupRigFactory(draft=False)
        user = UserFactory()

        with pytest.raises(ValidationError) as ex:
            update_custom_jackup_rig(rig=rig, user=user, **CUSTOM_JACKUP_RIG_SERIALIZED_DRAFT_DATA)
        assert ex.value.message_dict == {'draft': ['Public rig cannot be marked as draft.']}

        mock_sync_custom_jackup_subarea_score_task.assert_not_called()


@pytest.mark.django_db
class TestCreateCustomDrillship:
    @pytest.mark.parametrize('data', (CUSTOM_DRILLSHIP_SERIALIZED_PUBLIC_DATA, CUSTOM_DRILLSHIP_SERIALIZED_DRAFT_DATA))
    def test_create_rig(self, data):
        tenant = TenantFactory()
        user = UserFactory()

        rig = create_custom_drillship(tenant=tenant, user=user, **data)

        assert rig.tenant == tenant
        assert rig.creator == user

        for field, value in data.items():
            assert getattr(rig, field) == value

    def test_assign_rig_to_project(self):
        tenant = TenantFactory()
        user = UserFactory()
        project = ProjectFactory(tenant=tenant)

        rig = create_custom_drillship(
            tenant=tenant, user=user, project=project.pk, **CUSTOM_DRILLSHIP_SERIALIZED_PUBLIC_DATA
        )

        assert rig.project == project

    def test_validate_project(self):
        tenant = TenantFactory()
        user = UserFactory()
        project = ProjectFactory()

        with pytest.raises(ValidationError) as ex:
            create_custom_drillship(
                tenant=tenant, user=user, project=project.pk, **CUSTOM_DRILLSHIP_SERIALIZED_PUBLIC_DATA
            )

        assert ex.value.message_dict == {'project': [f'Project {project.pk} doesn\'t exist']}


@pytest.mark.django_db
class TestUpdateCustomDrillship:
    @pytest.mark.parametrize(
        'data, draft',
        ((CUSTOM_DRILLSHIP_SERIALIZED_PUBLIC_DATA, False), (CUSTOM_DRILLSHIP_SERIALIZED_DRAFT_DATA, True)),
    )
    def test_update_custom_drillship(self, data, draft):
        rig = CustomDrillshipFactory(draft=draft)
        user = UserFactory()

        rig = update_custom_drillship(rig=rig, user=user, **data)
        rig = CustomDrillship.objects.get(pk=rig.pk)

        for field, value in data.items():
            assert getattr(rig, field) == value

    def test_cannot_mark_public_custom_drillship_as_draft(self):
        rig = CustomDrillshipFactory(draft=False)
        user = UserFactory()

        with pytest.raises(ValidationError) as ex:
            update_custom_drillship(rig=rig, user=user, **CUSTOM_DRILLSHIP_SERIALIZED_DRAFT_DATA)
        assert ex.value.message_dict == {'draft': ['Public rig cannot be marked as draft.']}


@pytest.mark.django_db
class TestSyncCustomJackupSubareaScore:
    def test_should_create_custom_jackup_subarea_score(
        self, expected_concept_cj70_subarea_scores: dict, concept_cj70: CustomJackupRig
    ):
        with pytest.raises(CustomJackupSubareaScore.DoesNotExist):
            CustomJackupSubareaScore.objects.get(rig=concept_cj70)

        jackup_subarea = sync_custom_jackup_subarea_score(concept_cj70)

        for field, expected_value in expected_concept_cj70_subarea_scores.items():
            assert getattr(jackup_subarea, field) == expected_value

        concept_cj70.refresh_from_db()
        assert concept_cj70.subarea_score == jackup_subarea

    def test_should_update_custom_jackup_subarea_score(
        self, expected_concept_cj70_subarea_scores: dict, concept_cj70: CustomJackupRig
    ):
        jackup_subarea = CustomJackupSubareaScoreFactory(rig=concept_cj70)

        updated_jackup_subarea_co2 = sync_custom_jackup_subarea_score(concept_cj70)

        assert updated_jackup_subarea_co2.pk == jackup_subarea.pk

        for field, expected_value in expected_concept_cj70_subarea_scores.items():
            assert getattr(updated_jackup_subarea_co2, field) == expected_value


@pytest.mark.django_db
class TestSyncCustomSemiSubareaScore:
    def test_should_create_custom_semi_subarea_score(
        self, expected_concept_cs60_subarea_scores: dict, concept_cs60: CustomSemiRig
    ):
        with pytest.raises(CustomSemiSubareaScore.DoesNotExist):
            CustomSemiSubareaScore.objects.get(rig=concept_cs60)

        semi_subarea = sync_custom_semi_subarea_score(concept_cs60)

        for field, expected_value in expected_concept_cs60_subarea_scores.items():
            assert getattr(semi_subarea, field) == expected_value

        concept_cs60.refresh_from_db()
        assert concept_cs60.subarea_score == semi_subarea

    def test_should_update_custom_semi_subarea_score(
        self, expected_concept_cs60_subarea_scores: dict, concept_cs60: CustomSemiRig
    ):
        semi_subarea = CustomSemiSubareaScoreFactory(rig=concept_cs60)

        updated_semi_subarea_co2 = sync_custom_semi_subarea_score(concept_cs60)

        assert updated_semi_subarea_co2.pk == semi_subarea.pk

        for field, expected_value in expected_concept_cs60_subarea_scores.items():
            assert getattr(updated_semi_subarea_co2, field) == expected_value


@pytest.mark.django_db
class TestSyncCustomJackupPlanCO2:
    @pytest.fixture
    def expected_jackup_co2_per_well_result(self) -> dict:
        return JackupCO2PerWellResult(
            operational_days=100.0,
            fuel=19.7,
            co2_td=62.4,
            fuel_winter=20.3,
            co2_winter_td=64.3,
            fuel_summer=19.1,
            co2_summer_td=60.5,
            move_time=447.0,
            total_days=6647.0,
            rig_day_rate_usd_d=300000.0,
            spread_cost=300000.0,
            fuel_per_day=19.7,
            co2=64.4,
            psv_trips=13.3,
            psv_fuel=129.0,
            psv_co2=408.9,
            psv_cost_usd=408536.0,
            helicopter_trips=14.02,
            helicopter_fuel=12.85,
            helicopter_co2=40.7,
            helicopter_cost_usd=40.7,
            move_fuel=141.0,
            tugs=3.0,
            tugs_cost=13500,
            total_fuel=1502.6,
            total_co2=4763.0,
            total_cost=42150828.0,
        )

    @pytest.fixture(autouse=True)
    def mock_calculate_custom_jackup_co2_per_well(
        self, mocker: MockerFixture, expected_jackup_co2_per_well_result: JackupCO2PerWellResult
    ) -> MagicMock:
        logger.warning("Test uses a mocked co2 per well calculation. Remove it when it's ready.")
        mock_calculate_custom_jackup_co2_per_well = mocker.patch(
            "apps.rigs.services.co2calculator.jackup.calculate_custom_jackup_co2_per_well"
        )
        mock_calculate_custom_jackup_co2_per_well.return_value = expected_jackup_co2_per_well_result
        return mock_calculate_custom_jackup_co2_per_well

    def assert_custom_jackup_plan_co2(
        self,
        *,
        custom_jackup_plan_co2: CustomJackupPlanCO2,
        expected_jackup_co2_per_well_result: dict,
        tvd_from_msl: int,
    ):
        assert custom_jackup_plan_co2.tugs_cost == expected_jackup_co2_per_well_result["tugs_cost"] * 2
        assert custom_jackup_plan_co2.helicopter_trips == expected_jackup_co2_per_well_result["helicopter_trips"] * 2
        assert custom_jackup_plan_co2.helicopter_fuel == expected_jackup_co2_per_well_result["helicopter_fuel"] * 2
        assert custom_jackup_plan_co2.helicopter_co2 == expected_jackup_co2_per_well_result["helicopter_co2"] * 2
        assert custom_jackup_plan_co2.helicopter_cost == expected_jackup_co2_per_well_result["helicopter_cost_usd"] * 2
        assert custom_jackup_plan_co2.psv_trips == expected_jackup_co2_per_well_result["psv_trips"] * 2
        assert custom_jackup_plan_co2.psv_fuel == expected_jackup_co2_per_well_result["psv_fuel"] * 2
        assert custom_jackup_plan_co2.psv_cost == expected_jackup_co2_per_well_result["psv_cost_usd"] * 2
        assert custom_jackup_plan_co2.psv_co2 == expected_jackup_co2_per_well_result["psv_co2"] * 2
        assert custom_jackup_plan_co2.total_fuel == expected_jackup_co2_per_well_result["total_fuel"] * 2
        assert custom_jackup_plan_co2.total_cost == expected_jackup_co2_per_well_result["total_cost"] * 2
        assert custom_jackup_plan_co2.total_co2 == expected_jackup_co2_per_well_result["total_co2"] * 2
        assert custom_jackup_plan_co2.cost_per_meter == (expected_jackup_co2_per_well_result["total_cost"]) * 2 / (
            tvd_from_msl * 2
        )
        assert custom_jackup_plan_co2.total_days == (expected_jackup_co2_per_well_result["total_days"]) * 2

    def test_should_create_custom_jackup_plan_co2(
        self,
        expected_concept_cj70_subarea_scores: dict,
        expected_jackup_co2_per_well_result: dict,
        concept_cj70: CustomJackupRig,
    ):
        CustomJackupSubareaScoreFactory(rig=concept_cj70, **expected_concept_cj70_subarea_scores)
        plan = PlanFactory()
        tvd_from_msl = 300
        PlanWellRelationFactory.create_batch(2, plan=plan, well__tvd_from_msl=tvd_from_msl)
        PlanWellRelationFactory()

        custom_jackup_plan_co2 = sync_custom_jackup_plan_co2(
            custom_jackup_rig=concept_cj70,
            plan=plan,
        )

        self.assert_custom_jackup_plan_co2(
            custom_jackup_plan_co2=custom_jackup_plan_co2,
            expected_jackup_co2_per_well_result=expected_jackup_co2_per_well_result,
            tvd_from_msl=tvd_from_msl,
        )

    def test_should_update_custom_jackup_plan_co2(
        self,
        expected_concept_cj70_subarea_scores: dict,
        expected_jackup_co2_per_well_result: dict,
        concept_cj70: CustomJackupRig,
    ):
        CustomJackupSubareaScoreFactory(rig=concept_cj70, **expected_concept_cj70_subarea_scores)
        plan = PlanFactory()
        tvd_from_msl = 300
        PlanWellRelationFactory.create_batch(2, plan=plan, well__tvd_from_msl=tvd_from_msl)
        PlanWellRelationFactory()
        custom_jackup_plan_co2 = CustomJackupPlanCO2Factory(rig=concept_cj70, plan=plan)

        updated_custom_jackup_plan_co2 = sync_custom_jackup_plan_co2(
            custom_jackup_rig=concept_cj70,
            plan=plan,
        )

        assert updated_custom_jackup_plan_co2.pk == custom_jackup_plan_co2.pk

        self.assert_custom_jackup_plan_co2(
            custom_jackup_plan_co2=updated_custom_jackup_plan_co2,
            expected_jackup_co2_per_well_result=expected_jackup_co2_per_well_result,
            tvd_from_msl=tvd_from_msl,
        )


@pytest.mark.django_db
class TestDeleteCustomRig:
    @pytest.mark.parametrize(
        'RigFactory',
        (CustomJackupRigFactory, CustomSemiRigFactory, CustomDrillshipFactory),
    )
    def test_can_delete_custom_rig(self, RigFactory):
        rig = RigFactory()

        delete_custom_rig(rig)

        with pytest.raises(ObjectDoesNotExist):
            rig.refresh_from_db()

    @pytest.mark.parametrize(
        'RigFactory, reference_operation_rig',
        (
            (CustomJackupRigFactory, 'reference_operation_jackup'),
            (CustomSemiRigFactory, 'reference_operation_semi'),
            (CustomDrillshipFactory, 'reference_operation_drillship'),
        ),
    )
    def test_cannot_delete_custom_rig(self, RigFactory, reference_operation_rig):
        project = ProjectFactory()
        rig = RigFactory(project=project)
        data = {
            "reference_operation_jackup": None,
            "reference_operation_semi": None,
            "reference_operation_drillship": None,
            reference_operation_rig: rig,
        }
        PlanFactory(
            name="Test plan",
            project=project,
            **data,
        )

        with pytest.raises(ValidationError) as ex:
            delete_custom_rig(rig)
        assert ex.value.messages == [
            'Rig cannot be deleted right now. Rig is used as a reference rig in plan "Test plan".'
        ]


@pytest.mark.django_db
class TestSyncCustomSemiPlanCO2:
    @pytest.fixture
    def expected_semi_co2_per_well_result(self) -> dict:
        return SemiCO2PerWellResult(
            operational_days=45.540000,
            transit_time=0.31944444,
            total_days=45.85944444,
            rig_day_rate_usd_d=300000,
            spread_cost=350000,
            rig_fuel_per_day=51.30000000,
            rig_total_fuel=2308.50000000,
            rig_total_co2=7317.94500000,
            psv_trips=9.758571428571429,
            psv_fuel=94.739464285389,
            psv_co2=300.32410178468314,
            psv_cost_usd=300076.0714227163,
            helicopter_trips=10.148914285714286,
            helicopter_fuel=9.303171428909724,
            helicopter_co2=29.39802171535473,
            helicopter_cost_usd=120095.4857149623,
            ahv_fuel=0,
            ahv_cost=0,
            transit_fuel=19.76944444,
            tugs=0,
            tugs_cost=0,
            total_fuel=2432.3120801542987,
            total_co2=7710.336262374838,
            total_cost=31813939.02935648,
            logistic_cost=420171.5571376786,
            move_cost=229780.6637728,
            total_rig_and_spread_cost=29808638.886,
            total_fuel_cost=2724189.5297728144,
            transit_co2=62.6691388748,
            support_co2=329.72212350003787,
        )

    @pytest.fixture(autouse=True)
    def mock_calculate_custom_semi_co2_per_well(
        self, mocker: MockerFixture, expected_semi_co2_per_well_result: dict
    ) -> MagicMock:
        logger.warning("Test uses a mocked co2 per well calculation. Remove it when it's ready.")
        mock_calculate_custom_semi_dp_co2_per_well = mocker.patch(
            "apps.rigs.services.co2calculator.semi.calculate_custom_semi_dp_co2_per_well"
        )
        mock_calculate_custom_semi_dp_co2_per_well.return_value = expected_semi_co2_per_well_result
        return mock_calculate_custom_semi_dp_co2_per_well

    def assert_custom_semi_plan_co2(
        self, *, custom_semi_plan_co2: CustomSemiPlanCO2, expected_semi_co2_per_well_result: dict, tvd_from_msl: int
    ):
        assert custom_semi_plan_co2.ahv_cost == expected_semi_co2_per_well_result["ahv_cost"] * 2
        assert custom_semi_plan_co2.helicopter_trips == expected_semi_co2_per_well_result["helicopter_trips"] * 2
        assert custom_semi_plan_co2.helicopter_fuel == expected_semi_co2_per_well_result["helicopter_fuel"] * 2
        assert custom_semi_plan_co2.helicopter_co2 == expected_semi_co2_per_well_result["helicopter_co2"] * 2
        assert custom_semi_plan_co2.helicopter_cost == expected_semi_co2_per_well_result["helicopter_cost_usd"] * 2
        assert custom_semi_plan_co2.psv_trips == expected_semi_co2_per_well_result["psv_trips"] * 2
        assert custom_semi_plan_co2.psv_fuel == expected_semi_co2_per_well_result["psv_fuel"] * 2
        assert custom_semi_plan_co2.psv_cost == expected_semi_co2_per_well_result["psv_cost_usd"] * 2
        assert custom_semi_plan_co2.psv_co2 == expected_semi_co2_per_well_result["psv_co2"] * 2
        assert custom_semi_plan_co2.tugs_cost == expected_semi_co2_per_well_result["tugs_cost"] * 2
        assert custom_semi_plan_co2.total_fuel == expected_semi_co2_per_well_result["total_fuel"] * 2
        assert custom_semi_plan_co2.total_cost == expected_semi_co2_per_well_result["total_cost"] * 2
        assert custom_semi_plan_co2.total_co2 == expected_semi_co2_per_well_result["total_co2"] * 2
        assert custom_semi_plan_co2.total_logistic_cost == expected_semi_co2_per_well_result["logistic_cost"] * 2
        assert custom_semi_plan_co2.total_move_cost == expected_semi_co2_per_well_result["move_cost"] * 2
        assert custom_semi_plan_co2.total_fuel_cost == expected_semi_co2_per_well_result["total_fuel_cost"] * 2
        assert custom_semi_plan_co2.total_transit_co2 == expected_semi_co2_per_well_result["transit_co2"] * 2
        assert custom_semi_plan_co2.total_support_co2 == expected_semi_co2_per_well_result["support_co2"] * 2
        assert (
            custom_semi_plan_co2.total_rig_and_spread_cost
            == expected_semi_co2_per_well_result["total_rig_and_spread_cost"] * 2
        )
        assert custom_semi_plan_co2.cost_per_meter == (expected_semi_co2_per_well_result["total_cost"]) * 2 / (
            tvd_from_msl * 2
        )
        assert custom_semi_plan_co2.total_days == expected_semi_co2_per_well_result["total_days"] * 2

    def test_should_create_custom_semi_plan_co2(
        self,
        expected_concept_cs60_subarea_scores: dict,
        expected_semi_co2_per_well_result: dict,
        concept_cs60: CustomSemiRig,
    ):
        CustomSemiSubareaScoreFactory(rig=concept_cs60, **expected_concept_cs60_subarea_scores)
        plan = PlanFactory()
        tvd_from_msl = 400
        PlanWellRelationFactory.create_batch(2, plan=plan, well__tvd_from_msl=tvd_from_msl)
        PlanWellRelationFactory()

        custom_semi_plan_co2 = sync_custom_semi_plan_co2(
            custom_semi_rig=concept_cs60,
            plan=plan,
        )

        self.assert_custom_semi_plan_co2(
            custom_semi_plan_co2=custom_semi_plan_co2,
            expected_semi_co2_per_well_result=expected_semi_co2_per_well_result,
            tvd_from_msl=tvd_from_msl,
        )

    def test_should_update_custom_semi_plan_co2(
        self,
        expected_concept_cs60_subarea_scores: dict,
        expected_semi_co2_per_well_result: dict,
        concept_cs60: CustomSemiRig,
    ):
        CustomSemiSubareaScoreFactory(rig=concept_cs60, **expected_concept_cs60_subarea_scores)
        plan = PlanFactory()
        tvd_from_msl = 400
        PlanWellRelationFactory.create_batch(2, plan=plan, well__tvd_from_msl=tvd_from_msl)
        PlanWellRelationFactory()
        custom_semi_plan_co2 = CustomSemiPlanCO2Factory(rig=concept_cs60, plan=plan)

        updated_custom_semi_plan_co2 = sync_custom_semi_plan_co2(
            custom_semi_rig=concept_cs60,
            plan=plan,
        )

        assert updated_custom_semi_plan_co2.pk == custom_semi_plan_co2.pk

        self.assert_custom_semi_plan_co2(
            custom_semi_plan_co2=updated_custom_semi_plan_co2,
            expected_semi_co2_per_well_result=expected_semi_co2_per_well_result,
            tvd_from_msl=tvd_from_msl,
        )
