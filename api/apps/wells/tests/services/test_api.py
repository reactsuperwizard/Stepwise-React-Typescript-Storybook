from datetime import date, datetime, timedelta
from typing import Callable
from unittest.mock import MagicMock, call

import pytest
import pytz
from django.core.exceptions import ValidationError
from pytest_mock import MockerFixture

from apps.emissions.factories import (
    AssetFactory,
    BaselineInputFactory,
    CompleteHelicopterUseFactory,
    CompleteVesselUseFactory,
    CustomModeFactory,
    CustomPhaseFactory,
    EmissionReductionInitiativeFactory,
    EmissionReductionInitiativeInputFactory,
    ExternalEnergySupplyFactory,
    MaterialTypeFactory,
    PlannedHelicopterUseFactory,
    PlannedVesselUseFactory,
    VesselTypeFactory,
    WellCompleteStepMaterialFactory,
    WellPlannedStepMaterialFactory,
)
from apps.emissions.models import AssetSeason, EmissionReductionInitiativeType, MaterialCategory
from apps.monitors.factories import MonitorFunctionFactory, MonitorFunctionValueFactory
from apps.monitors.models import MonitorFunctionType
from apps.projects.factories import PlanWellRelationFactory, ProjectFactory
from apps.tenants.factories import TenantFactory, UserFactory
from apps.wells.factories import (
    CustomWellFactory,
    WellPlannerCompleteStepFactory,
    WellPlannerFactory,
    WellPlannerPlannedStepFactory,
)
from apps.wells.models import CustomWell, WellPlannerCompleteStep, WellPlannerPlannedStep, WellPlannerWizardStep
from apps.wells.services.api import (
    DurationHoursResult,
    WellPlannerCo2Dataset,
    WellPlannerMeasuredSummary,
    WellPlannerMeasurementDataset,
    WellPlannerStepCo2Dataset,
    WellPlannerStepMaterialData,
    approve_well_planner_complete_helicopter_uses,
    approve_well_planner_complete_steps,
    approve_well_planner_complete_vessel_uses,
    available_emission_reduction_initiatives,
    complete_well_planner_planning,
    complete_well_planner_reviewing,
    copy_well_planner_step,
    create_custom_well,
    create_well_planner_complete_step,
    create_well_planner_planned_step,
    delete_custom_well,
    delete_well_planner_complete_step,
    delete_well_planner_planned_step,
    duplicate_well_planner_complete_step,
    duplicate_well_planner_planned_step,
    get_well_planner_daily_co2_dataset,
    get_well_planner_daily_measured_co2_dataset,
    get_well_planner_hourly_co2_dataset,
    get_well_planner_hourly_measured_co2_dataset,
    get_well_planner_measured_co2_dataset,
    get_well_planner_measured_summary,
    get_well_planner_measurement_dataset,
    get_well_planner_planned_co2_dataset,
    get_well_planner_saved_co2_dataset,
    get_well_planner_summary,
    move_well_planner_complete_step,
    move_well_planner_planned_step,
    split_duration_into_hours,
    update_custom_well,
    update_well_planner_actual_start_date,
    update_well_planner_complete_step,
    update_well_planner_complete_step_emission_reduction_initiatives,
    update_well_planner_planned_step,
    update_well_planner_planned_step_emission_reduction_initiatives,
    validate_well_planner_step_data,
)
from apps.wells.services.co2calculator import WellPlannerStepCO2Result, multiply_well_planner_step_co2
from apps.wells.tests.fixtures import (
    CUSTOM_WELL_DRAFT_DATA,
    CUSTOM_WELL_PUBLIC_DATA,
    WELL_PLANNER_COMPLETE_STEP_DATA,
    WELL_PLANNER_PLANNED_STEP_DATA,
)


@pytest.fixture
def mocked_well_planner_step_co2() -> WellPlannerStepCO2Result:
    return WellPlannerStepCO2Result(
        base=1.0,
        baseline=2.0,
        target=3.0,
        rig=4.0,
        vessels=5.0,
        helicopters=6.0,
        cement=8.0,
        steel=7.0,
        external_energy_supply=9.0,
        emission_reduction_initiatives=[
            {
                "emission_reduction_initiative": EmissionReductionInitiativeFactory(),
                "value": 10.0,
            },
        ],
    )


@pytest.fixture
def mock_calculate_well_planner_step_co2(
    mocker: MockerFixture, mocked_well_planner_step_co2: WellPlannerStepCO2Result
) -> MagicMock:
    mock_calculate_well_planner_step_co2 = mocker.patch(
        "apps.wells.services.api.calculate_well_planner_step_co2",
        return_value=mocked_well_planner_step_co2,
    )
    return mock_calculate_well_planner_step_co2


@pytest.fixture
def mock_calculate_measured_well_planner_step_co2(
    mocker: MockerFixture, mocked_well_planner_step_co2: WellPlannerStepCO2Result
) -> MagicMock:
    mock_calculate_measured_well_planner_step_co2 = mocker.patch(
        "apps.wells.services.api.calculate_measured_well_planner_step_co2",
        return_value=mocked_well_planner_step_co2,
    )
    return mock_calculate_measured_well_planner_step_co2


@pytest.mark.django_db
class TestCreateCustomWell:
    @pytest.mark.parametrize('data', (CUSTOM_WELL_PUBLIC_DATA, CUSTOM_WELL_DRAFT_DATA))
    def test_create_well(self, data: dict):
        tenant = TenantFactory()
        user = UserFactory()

        well = create_custom_well(tenant=tenant, user=user, **data)

        assert well.tenant == tenant
        assert well.creator == user

        for field, value in data.items():
            assert getattr(well, field) == value

    def test_assign_well_to_project(self):
        tenant = TenantFactory()
        user = UserFactory()
        project = ProjectFactory(tenant=tenant)

        well = create_custom_well(tenant=tenant, user=user, project=project.pk, **CUSTOM_WELL_PUBLIC_DATA)

        assert project.wells.get() == well

    def test_validate_project(self):
        tenant = TenantFactory()
        user = UserFactory()
        project = ProjectFactory()

        with pytest.raises(ValidationError) as ex:
            create_custom_well(tenant=tenant, user=user, project=project.pk, **CUSTOM_WELL_PUBLIC_DATA)

        assert ex.value.message_dict == {'project': [f'Project {project.pk} doesn\'t exist']}


@pytest.mark.django_db
class TestUpdateCustomWell:
    @pytest.fixture
    def mock_sync_all_custom_well_co2_calculations(self, mocker: MockerFixture):
        mock_sync_all_custom_well_co2_calculations = mocker.patch(
            "apps.rigs.tasks.sync_all_custom_well_co2_calculations_task.delay"
        )
        return mock_sync_all_custom_well_co2_calculations

    @pytest.mark.parametrize(
        'data,should_sync_calculations', ((CUSTOM_WELL_DRAFT_DATA, False), (CUSTOM_WELL_PUBLIC_DATA, True))
    )
    def test_update_custom_well(
        self, mock_sync_all_custom_well_co2_calculations: MagicMock, should_sync_calculations: bool, data: dict
    ):
        well = CustomWellFactory()
        user = UserFactory()

        well = update_custom_well(well=well, user=user, **data)
        well = CustomWell.objects.get(pk=well.pk)

        for field, value in data.items():
            assert getattr(well, field) == value

        assert mock_sync_all_custom_well_co2_calculations.called is should_sync_calculations

    def test_delete_custom_well(self, mock_sync_all_plan_co2_calculations_task: MagicMock):
        well = CustomWellFactory()
        plan_well_relation_1 = PlanWellRelationFactory(well=well)
        plan_well_relation_2 = PlanWellRelationFactory(well=well)

        user = UserFactory()

        delete_custom_well(well=well, user=user)

        with pytest.raises(CustomWell.DoesNotExist):
            CustomWell.objects.get(pk=well.pk)

        assert mock_sync_all_plan_co2_calculations_task.call_args_list == [
            call(plan_well_relation_1.plan.pk),
            call(plan_well_relation_2.plan.pk),
        ]


@pytest.mark.django_db
class TestValidateWellPlannerStepData:
    @pytest.fixture()
    def emission_reduction_initiative_initial_data(self) -> dict:
        asset = AssetFactory()
        well_planner = WellPlannerFactory(asset=asset, planned_start_date=date(2022, 6, 1))
        phase = CustomPhaseFactory(asset=asset)
        mode = CustomModeFactory(asset=asset)
        season = AssetSeason.SUMMER
        BaselineInputFactory(phase=phase, mode=mode, season=season, baseline=well_planner.baseline)
        return dict(well_planner=well_planner, phase=phase, mode=mode, season=season)

    @pytest.mark.parametrize(
        "parameter,Factory,error_message",
        (
            ("phase", CustomPhaseFactory, 'Invalid combination of phase, mode and season used.'),
            ("mode", CustomModeFactory, 'Invalid combination of phase, mode and season used.'),
        ),
    )
    def test_should_raise_validation_error_for_missing_baseline_input(
        self,
        parameter: str,
        Factory: Callable,
        error_message: dict,
    ):
        well_planner = WellPlannerFactory()
        phase = CustomPhaseFactory(asset=well_planner.asset)
        mode = CustomModeFactory(asset=well_planner.asset)
        season = AssetSeason.SUMMER
        BaselineInputFactory(phase=phase, mode=mode, season=season, baseline=well_planner.baseline)
        data = {
            "phase": phase,
            "mode": mode,
            "season": season,
            "emission_reduction_initiatives": [],
            parameter: Factory(),
        }

        with pytest.raises(ValidationError) as ex:
            validate_well_planner_step_data(well_planner=well_planner, **data)

        assert ex.value.message == error_message

    @pytest.mark.parametrize(
        "parameter,Factory,error_message",
        (
            (
                "materials",
                lambda: [
                    WellPlannerStepMaterialData(
                        material_type=MaterialTypeFactory(category=MaterialCategory.CEMENT),
                        quantity=100.0,
                        quota=False,
                    ),
                ],
                {"materials": ["Chosen material types are not  valid choices."]},
            ),
            (
                "emission_reduction_initiatives",
                lambda: [EmissionReductionInitiativeFactory()],
                {"emission_reduction_initiatives": ["Chosen energy reduction initiative is not a valid choice."]},
            ),
        ),
    )
    def test_should_raise_validation_error_for_different_asset_or_tenant(
        self,
        parameter: str,
        Factory: Callable,
        error_message: dict,
    ):
        well_planner = WellPlannerFactory()
        phase = CustomPhaseFactory(asset=well_planner.asset)
        mode = CustomModeFactory(asset=well_planner.asset)
        season = AssetSeason.SUMMER
        BaselineInputFactory(phase=phase, mode=mode, season=season, baseline=well_planner.baseline)
        data = {
            "phase": phase,
            "mode": mode,
            "season": season,
            "emission_reduction_initiatives": [],
            "materials": [],
            parameter: Factory(),
        }

        with pytest.raises(ValidationError) as ex:
            validate_well_planner_step_data(well_planner=well_planner, **data)

        assert ex.value.message_dict == error_message

    def test_emission_reduction_initiative_with_invalid_emission_management_plan(
        self, emission_reduction_initiative_initial_data: dict
    ):
        emission_reduction_initiative = EmissionReductionInitiativeFactory()
        data = {
            **emission_reduction_initiative_initial_data,
            "emission_reduction_initiatives": [emission_reduction_initiative],
        }

        with pytest.raises(ValidationError) as ex:
            validate_well_planner_step_data(**data)

        assert ex.value.message_dict == {
            'emission_reduction_initiatives': ['Chosen energy reduction initiative is not a valid choice.'],
        }

    def test_emission_reduction_initiative_with_future_deployment_date(
        self, emission_reduction_initiative_initial_data: dict
    ):
        well_planner = emission_reduction_initiative_initial_data["well_planner"]
        emission_reduction_initiative = EmissionReductionInitiativeFactory(
            emission_management_plan=well_planner.emission_management_plan,
            deployment_date=date(2023, 1, 1),
        )
        data = {
            **emission_reduction_initiative_initial_data,
            "emission_reduction_initiatives": [emission_reduction_initiative],
        }

        with pytest.raises(ValidationError) as ex:
            validate_well_planner_step_data(**data)

        assert ex.value.message_dict == {
            "emission_reduction_initiatives": [
                f"Energy reduction initiative \"{emission_reduction_initiative.name}\" is not deployed yet."
            ]
        }

    def test_deleted_emission_reduction_initiative(self, emission_reduction_initiative_initial_data: dict):
        well_planner = emission_reduction_initiative_initial_data["well_planner"]
        emission_reduction_initiative = EmissionReductionInitiativeFactory(
            emission_management_plan=well_planner.emission_management_plan,
            deleted=True,
        )
        data = {
            **emission_reduction_initiative_initial_data,
            "emission_reduction_initiatives": [emission_reduction_initiative],
        }

        with pytest.raises(ValidationError) as ex:
            validate_well_planner_step_data(**data)

        assert ex.value.message_dict == {
            "emission_reduction_initiatives": ["Chosen energy reduction initiative is not a valid choice."]
        }

    def test_should_raise_for_deleted_material_type(self):
        well_planner = WellPlannerFactory()
        phase = CustomPhaseFactory(asset=well_planner.asset)
        mode = CustomModeFactory(asset=well_planner.asset)
        season = AssetSeason.SUMMER
        material_type = MaterialTypeFactory(tenant=well_planner.asset.tenant, deleted=True)
        BaselineInputFactory(phase=phase, mode=mode, season=season, baseline=well_planner.baseline)

        data = {
            "phase": phase,
            "mode": mode,
            "season": season,
            "materials": [
                WellPlannerStepMaterialData(
                    material_type=material_type,
                    quantity=100.0,
                    quota=True,
                ),
            ],
        }

        with pytest.raises(ValidationError) as ex:
            validate_well_planner_step_data(well_planner=well_planner, **data)

        assert ex.value.message_dict == {"materials": ["Chosen material types are not  valid choices."]}


@pytest.fixture
def mocked_calculate_planned_emissions(mocker: MockerFixture):
    return mocker.patch("apps.wells.services.api.calculate_planned_emissions")


@pytest.mark.django_db
class TestCreateWellPlannerPlannedStep:
    def test_should_create_well_planner_planned_step(self, mocked_calculate_planned_emissions: MagicMock):
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=WellPlannerWizardStep.WELL_PLANNING)
        ExternalEnergySupplyFactory(asset=well_planner.asset)
        emission_reduction_initiatives = EmissionReductionInitiativeFactory.create_batch(
            2, emission_management_plan=well_planner.emission_management_plan
        )
        phase = CustomPhaseFactory(asset=well_planner.asset)
        mode = CustomModeFactory(asset=well_planner.asset)
        first_material_type, second_material_type = MaterialTypeFactory.create_batch(
            2, tenant=well_planner.asset.tenant
        )
        materials_data = [
            WellPlannerStepMaterialData(material_type=first_material_type, quantity=10, quota=False),
            WellPlannerStepMaterialData(material_type=second_material_type, quantity=15, quota=True),
        ]
        BaselineInputFactory(
            baseline=well_planner.baseline, phase=phase, mode=mode, season=WELL_PLANNER_PLANNED_STEP_DATA["season"]
        )

        data = {
            **WELL_PLANNER_PLANNED_STEP_DATA,
            "phase": phase,
            "mode": mode,
            "well_planner": well_planner,
        }

        planned_step = create_well_planner_planned_step(
            user=user,
            emission_reduction_initiatives=emission_reduction_initiatives,
            materials=materials_data,
            **data,
        )

        assert planned_step.pk is not None

        for field, value in data.items():
            assert getattr(planned_step, field) == value

        assert list(planned_step.emission_reduction_initiatives.all()) == emission_reduction_initiatives

        for material_data, material in zip(materials_data, planned_step.materials.order_by('pk')):
            for field, value in material_data.items():
                assert getattr(material, field) == value

        mocked_calculate_planned_emissions.assert_called_once_with(well_planner)

    @pytest.mark.parametrize(
        'current_step', (set(WellPlannerWizardStep.values) - {WellPlannerWizardStep.WELL_PLANNING})
    )
    def test_should_raise_error_for_invalid_current_step(self, current_step: WellPlannerWizardStep):
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=current_step)

        with pytest.raises(ValidationError) as ex:
            create_well_planner_planned_step(
                well_planner=well_planner,
                user=user,
                emission_reduction_initiatives=[],
                phase=CustomPhaseFactory(asset=well_planner.asset),
                mode=CustomModeFactory(asset=well_planner.asset),
                **WELL_PLANNER_PLANNED_STEP_DATA,
            )

        assert ex.value.message == "Phase cannot be created right now."

    def test_should_create_well_planner_planned_step_without_optional_parameters(
        self,
    ):
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=WellPlannerWizardStep.WELL_PLANNING)
        ExternalEnergySupplyFactory(asset=well_planner.asset)
        phase = CustomPhaseFactory(asset=well_planner.asset)
        mode = CustomModeFactory(asset=well_planner.asset)
        BaselineInputFactory(
            baseline=well_planner.baseline, phase=phase, mode=mode, season=WELL_PLANNER_PLANNED_STEP_DATA["season"]
        )
        planned_step = create_well_planner_planned_step(
            well_planner=well_planner,
            user=user,
            phase=phase,
            mode=mode,
            emission_reduction_initiatives=[],
            materials=[],
            **WELL_PLANNER_PLANNED_STEP_DATA,
        )

        assert planned_step.pk is not None
        assert planned_step.well_planner == well_planner

        for field, value in WELL_PLANNER_PLANNED_STEP_DATA.items():
            assert getattr(planned_step, field) == value

        assert planned_step.emission_reduction_initiatives.count() == 0


@pytest.mark.django_db
class TestUpdateWellPlannerPlannedStep:
    def test_should_update_well_planner_planned_step(self, mocked_calculate_planned_emissions: MagicMock):
        user = UserFactory()
        asset = AssetFactory()
        ExternalEnergySupplyFactory(asset=asset)
        planned_step = WellPlannerPlannedStepFactory(
            well_planner__asset=asset, well_planner__current_step=WellPlannerWizardStep.WELL_PLANNING
        )
        old_emission_reduction_initiatives = EmissionReductionInitiativeFactory.create_batch(
            2, emission_management_plan=planned_step.well_planner.emission_management_plan
        )
        planned_step.emission_reduction_initiatives.add(*old_emission_reduction_initiatives)

        new_emission_reduction_initiatives = EmissionReductionInitiativeFactory.create_batch(
            2, emission_management_plan=planned_step.well_planner.emission_management_plan
        )
        old_material, _ = WellPlannedStepMaterialFactory.create_batch(2, step=planned_step)
        material_type = MaterialTypeFactory(tenant=asset.tenant)

        materials_data = [
            WellPlannerStepMaterialData(id=old_material.pk, material_type=material_type, quantity=10.0, quota=False),
            WellPlannerStepMaterialData(material_type=old_material.material_type, quantity=99.9, quota=True),
            WellPlannerStepMaterialData(material_type=material_type, quantity=15.0, quota=True),
        ]

        phase = CustomPhaseFactory(asset=asset)
        mode = CustomModeFactory(asset=asset)
        BaselineInputFactory(
            baseline=planned_step.well_planner.baseline,
            phase=phase,
            mode=mode,
            season=WELL_PLANNER_PLANNED_STEP_DATA["season"],
        )
        data = {
            **WELL_PLANNER_PLANNED_STEP_DATA,
            "phase": phase,
            "mode": mode,
        }

        updated_planned_step = update_well_planner_planned_step(
            planned_step=planned_step,
            user=user,
            emission_reduction_initiatives=new_emission_reduction_initiatives,
            materials=materials_data,
            **data,
        )

        assert updated_planned_step.pk == planned_step.pk
        assert updated_planned_step.well_planner == planned_step.well_planner

        for field, value in data.items():
            assert getattr(updated_planned_step, field) == value

        assert list(updated_planned_step.emission_reduction_initiatives.all()) == new_emission_reduction_initiatives

        for material_data, material in zip(materials_data, updated_planned_step.materials.order_by('pk')):
            for field, value in material_data.items():
                assert getattr(material, field) == value

        mocked_calculate_planned_emissions.assert_called_once_with(planned_step.well_planner)

    def test_should_update_well_planner_planned_step_without_optional_data(
        self,
    ):
        user = UserFactory()
        asset = AssetFactory()
        ExternalEnergySupplyFactory(asset=asset)
        planned_step = WellPlannerPlannedStepFactory(
            well_planner__asset=asset, well_planner__current_step=WellPlannerWizardStep.WELL_PLANNING
        )
        old_emission_reduction_initiatives = EmissionReductionInitiativeFactory.create_batch(
            2, emission_management_plan=planned_step.well_planner.emission_management_plan
        )
        planned_step.emission_reduction_initiatives.add(*old_emission_reduction_initiatives)

        phase = CustomPhaseFactory(asset=asset)
        mode = CustomModeFactory(asset=asset)
        BaselineInputFactory(
            baseline=planned_step.well_planner.baseline,
            phase=phase,
            mode=mode,
            season=WELL_PLANNER_PLANNED_STEP_DATA["season"],
        )

        updated_planned_step = update_well_planner_planned_step(
            planned_step=planned_step,
            user=user,
            phase=phase,
            mode=mode,
            emission_reduction_initiatives=[],
            materials=[],
            **WELL_PLANNER_PLANNED_STEP_DATA,
        )

        assert updated_planned_step.pk == planned_step.pk
        assert updated_planned_step.well_planner == planned_step.well_planner

        for field, value in WELL_PLANNER_PLANNED_STEP_DATA.items():
            assert getattr(updated_planned_step, field) == value

        assert updated_planned_step.emission_reduction_initiatives.count() == 0

    @pytest.mark.parametrize(
        'current_step', (set(WellPlannerWizardStep.values) - {WellPlannerWizardStep.WELL_PLANNING})
    )
    def test_should_raise_error_for_invalid_current_step(self, current_step: WellPlannerWizardStep):
        user = UserFactory()
        asset = AssetFactory()
        planned_step = WellPlannerPlannedStepFactory(well_planner__asset=asset, well_planner__current_step=current_step)

        with pytest.raises(ValidationError) as ex:
            update_well_planner_planned_step(
                planned_step=planned_step,
                user=user,
                emission_reduction_initiatives=[],
                phase=CustomPhaseFactory(asset=asset),
                mode=CustomModeFactory(asset=asset),
                **WELL_PLANNER_PLANNED_STEP_DATA,
            )

        assert ex.value.message == "Phase cannot be updated right now."


@pytest.mark.django_db
class TestDeleteWellPlannerPlannedStep:
    def test_should_delete_well_planner_planned_step(self, mocked_calculate_planned_emissions: MagicMock):
        user = UserFactory()
        planned_step = WellPlannerPlannedStepFactory(well_planner__current_step=WellPlannerWizardStep.WELL_PLANNING)

        delete_well_planner_planned_step(planned_step=planned_step, user=user)

        assert not WellPlannerPlannedStep.objects.filter(pk=planned_step.pk).exists()

        mocked_calculate_planned_emissions.assert_called_once_with(planned_step.well_planner)

    @pytest.mark.parametrize(
        'current_step', (set(WellPlannerWizardStep.values) - {WellPlannerWizardStep.WELL_PLANNING})
    )
    def test_should_raise_error_for_invalid_current_step(self, current_step: WellPlannerWizardStep):
        user = UserFactory()
        planned_step = WellPlannerPlannedStepFactory(well_planner__current_step=current_step)

        with pytest.raises(ValidationError) as ex:
            delete_well_planner_planned_step(planned_step=planned_step, user=user)

        assert ex.value.message == "Phase cannot be deleted right now."


@pytest.mark.django_db
def test_get_well_planner_daily_co2_dataset(mocked_well_planner_step_co2: WellPlannerStepCO2Result):
    step_duration = 0.5
    day_duration = 0.25
    assert get_well_planner_daily_co2_dataset(
        step_co2=mocked_well_planner_step_co2,
        step_duration=step_duration,
        plan_start_date=datetime(2022, 6, 1, 0),
        step_waiting_duration=3.75,
    ) == [
        WellPlannerCo2Dataset(
            date=datetime(2022, 6, 4, 0, 0),
            **multiply_well_planner_step_co2(mocked_well_planner_step_co2, 1 / step_duration * day_duration),
        ),
        WellPlannerCo2Dataset(
            date=datetime(2022, 6, 5, 0, 0),
            **multiply_well_planner_step_co2(mocked_well_planner_step_co2, 1 / step_duration * day_duration),
        ),
    ]


@pytest.mark.django_db
class TestGetWellPlannerHourlyCO2Dataset:
    def test_filter_co2_dataset_by_start_end_dates(self, mocked_well_planner_step_co2: WellPlannerStepCO2Result):
        start_date = datetime(2022, 6, 5, 1, 0)
        end_date = datetime(2022, 6, 5, 3, 0)
        step_duration = 0.5
        hour_duration = 1

        assert get_well_planner_hourly_co2_dataset(
            start_date=start_date,
            end_date=end_date,
            plan_start_date=datetime(2022, 6, 1, 0),
            step_co2=mocked_well_planner_step_co2,
            step_duration=step_duration,
            step_waiting_duration=3.75,
        ) == [
            WellPlannerCo2Dataset(
                date=datetime(2022, 6, 5, 1, 0),
                **multiply_well_planner_step_co2(mocked_well_planner_step_co2, 1 / step_duration / 24 * hour_duration),
            ),
            WellPlannerCo2Dataset(
                date=datetime(2022, 6, 5, 2, 0),
                **multiply_well_planner_step_co2(mocked_well_planner_step_co2, 1 / step_duration / 24 * hour_duration),
            ),
            WellPlannerCo2Dataset(
                date=datetime(2022, 6, 5, 3, 0),
                **multiply_well_planner_step_co2(mocked_well_planner_step_co2, 1 / step_duration / 24 * hour_duration),
            ),
        ]

    @pytest.mark.parametrize(
        'plan_start_date, step_duration, step_waiting_duration',
        (
            (datetime(2022, 5, 1, 0), 10, 20),
            (datetime(2022, 6, 1, 0), 10, 20),
        ),
    )
    def test_step_outside_start_end_dates(
        self,
        plan_start_date: datetime,
        step_duration: float,
        step_waiting_duration: float,
        mocked_well_planner_step_co2: WellPlannerStepCO2Result,
    ):
        start_date = datetime(2022, 6, 4, 0, 0)
        end_date = datetime(2022, 6, 6, 0, 0)

        assert (
            get_well_planner_hourly_co2_dataset(
                start_date=start_date,
                end_date=end_date,
                plan_start_date=plan_start_date,
                step_co2=mocked_well_planner_step_co2,
                step_duration=step_duration,
                step_waiting_duration=step_waiting_duration,
            )
            == []
        )


@pytest.mark.django_db
class TestGetWellPlannerPlannedCo2Dataset:
    @pytest.mark.parametrize(
        "step_1_data, step_2_data, step_3_data, step_4_data, step_5_data, improved",
        (
            (
                dict(duration=0.25, waiting_on_weather=100),
                dict(duration=0.125, waiting_on_weather=100),
                dict(duration=0.125, waiting_on_weather=100),
                dict(duration=0.625, waiting_on_weather=100),
                dict(duration=0.5, waiting_on_weather=100),
                False,
            ),
            (
                dict(improved_duration=0.5),
                dict(improved_duration=0.25),
                dict(improved_duration=0.25),
                dict(improved_duration=1.25),
                dict(improved_duration=1),
                True,
            ),
        ),
    )
    def test_calculate_planned_daily_co2_dataset(
        self,
        mock_calculate_well_planner_step_co2: MagicMock,
        mocked_well_planner_step_co2: WellPlannerStepCO2Result,
        step_1_data: dict,
        step_2_data: dict,
        step_3_data: dict,
        step_4_data: dict,
        step_5_data: dict,
        improved: bool,
    ):
        well_planner = WellPlannerFactory()
        well_planner_step_1 = WellPlannerPlannedStepFactory(well_planner=well_planner, **step_1_data)
        well_planner_step_2 = WellPlannerPlannedStepFactory(well_planner=well_planner, **step_2_data)
        well_planner_step_3 = WellPlannerPlannedStepFactory(well_planner=well_planner, **step_3_data)
        well_planner_step_4 = WellPlannerPlannedStepFactory(well_planner=well_planner, **step_4_data)
        well_planner_step_5 = WellPlannerPlannedStepFactory(well_planner=well_planner, **step_5_data)
        date = datetime.combine(well_planner.planned_start_date, datetime.min.time())

        expected_dataset = [
            WellPlannerStepCo2Dataset(
                date=date,
                step=well_planner_step_1,
                **mocked_well_planner_step_co2,
            ),
            WellPlannerStepCo2Dataset(
                date=date,
                step=well_planner_step_2,
                **mocked_well_planner_step_co2,
            ),
            WellPlannerStepCo2Dataset(
                date=date,
                step=well_planner_step_3,
                **mocked_well_planner_step_co2,
            ),
            WellPlannerStepCo2Dataset(
                date=date + timedelta(days=1),
                step=well_planner_step_4,
                **multiply_well_planner_step_co2(mocked_well_planner_step_co2, 0.8),
            ),
            WellPlannerStepCo2Dataset(
                date=date + timedelta(days=2),
                step=well_planner_step_4,
                **multiply_well_planner_step_co2(mocked_well_planner_step_co2, 0.2),
            ),
            WellPlannerStepCo2Dataset(
                date=date + timedelta(days=2),
                step=well_planner_step_5,
                **multiply_well_planner_step_co2(mocked_well_planner_step_co2, 0.75),
            ),
            WellPlannerStepCo2Dataset(
                date=date + timedelta(days=3),
                step=well_planner_step_5,
                **multiply_well_planner_step_co2(mocked_well_planner_step_co2, 0.25),
            ),
        ]

        dataset = get_well_planner_planned_co2_dataset(well_planner=well_planner, improved=improved)
        assert dataset == expected_dataset

    @pytest.mark.parametrize(
        "step_1_data, step_2_data, step_3_data, step_4_data, step_5_data, improved",
        (
            (
                dict(duration=0.25, waiting_on_weather=100),
                dict(duration=0.125, waiting_on_weather=100),
                dict(duration=0.125, waiting_on_weather=100),
                dict(duration=0.625, waiting_on_weather=100),
                dict(duration=0.5, waiting_on_weather=100),
                False,
            ),
            (
                dict(improved_duration=0.5),
                dict(improved_duration=0.25),
                dict(improved_duration=0.25),
                dict(improved_duration=1.25),
                dict(improved_duration=1),
                True,
            ),
        ),
    )
    def test_calculate_planned_hourly_co2_dataset(
        self,
        mock_calculate_well_planner_step_co2: MagicMock,
        mocked_well_planner_step_co2: WellPlannerStepCO2Result,
        step_1_data: dict,
        step_2_data: dict,
        step_3_data: dict,
        step_4_data: dict,
        step_5_data: dict,
        improved: bool,
    ):
        well_planner = WellPlannerFactory()
        WellPlannerPlannedStepFactory(well_planner=well_planner, **step_1_data)
        WellPlannerPlannedStepFactory(well_planner=well_planner, **step_2_data)
        well_planner_step_3 = WellPlannerPlannedStepFactory(well_planner=well_planner, **step_3_data)
        well_planner_step_4 = WellPlannerPlannedStepFactory(well_planner=well_planner, **step_4_data)
        WellPlannerPlannedStepFactory(well_planner=well_planner, **step_5_data)
        date = datetime.combine(well_planner.planned_start_date, datetime.min.time()).replace(tzinfo=pytz.UTC)

        expected_dataset = [
            WellPlannerStepCo2Dataset(
                date=date + timedelta(days=0, hours=22),
                step=well_planner_step_3,
                **multiply_well_planner_step_co2(mocked_well_planner_step_co2, 1 / 0.25 / 24),
            ),
            WellPlannerStepCo2Dataset(
                date=date + timedelta(days=0, hours=23),
                step=well_planner_step_3,
                **multiply_well_planner_step_co2(mocked_well_planner_step_co2, 1 / 0.25 / 24),
            ),
            WellPlannerStepCo2Dataset(
                date=date + timedelta(days=1, hours=0),
                step=well_planner_step_4,
                **multiply_well_planner_step_co2(mocked_well_planner_step_co2, 1 / 1.25 / 24),
            ),
            WellPlannerStepCo2Dataset(
                date=date + timedelta(days=1, hours=1),
                step=well_planner_step_4,
                **multiply_well_planner_step_co2(mocked_well_planner_step_co2, 1 / 1.25 / 24),
            ),
            WellPlannerStepCo2Dataset(
                date=date + timedelta(days=1, hours=2),
                step=well_planner_step_4,
                **multiply_well_planner_step_co2(mocked_well_planner_step_co2, 1 / 1.25 / 24),
            ),
        ]

        dataset = get_well_planner_planned_co2_dataset(
            well_planner=well_planner,
            improved=improved,
            start_date=date + timedelta(days=0, hours=22),
            end_date=date + timedelta(days=1, hours=2),
        )
        assert dataset == expected_dataset


@pytest.fixture
def mock_calculate_well_planner_co2_improvement(
    mocker: MockerFixture, mocked_well_planner_step_co2: WellPlannerStepCO2Result
) -> MagicMock:
    mock_calculate_well_planner_step_co2 = mocker.patch(
        "apps.wells.services.api.calculate_well_planner_co2_improvement",
        return_value=mocked_well_planner_step_co2,
    )
    return mock_calculate_well_planner_step_co2


@pytest.mark.django_db
class TestGetWellPlannerSavedCo2Dataset:
    def test_should_get_well_planner_saved_co2_dataset_without_improvement(
        self,
    ):
        well_planner = WellPlannerFactory()
        WellPlannerPlannedStepFactory(
            well_planner=well_planner, improved_duration=1.5, duration=0.75, waiting_on_weather=100
        )
        WellPlannerPlannedStepFactory(
            well_planner=well_planner, improved_duration=1.25, duration=0.625, waiting_on_weather=100
        )

        dataset = get_well_planner_saved_co2_dataset(well_planner=well_planner)
        assert dataset == []

    def test_calculate_daily_saved_co2_dataset(
        self,
        mock_calculate_well_planner_co2_improvement: MagicMock,
        mocked_well_planner_step_co2: WellPlannerStepCO2Result,
    ):
        well_planner = WellPlannerFactory()
        WellPlannerPlannedStepFactory(
            well_planner=well_planner, improved_duration=1.5, duration=1, waiting_on_weather=100
        )
        WellPlannerPlannedStepFactory(
            well_planner=well_planner, improved_duration=1.25, duration=0.75, waiting_on_weather=100
        )
        saved_duration = 0.75

        date = datetime.combine(well_planner.planned_start_date, datetime.min.time())

        expected_dataset = [
            WellPlannerCo2Dataset(
                date=date + timedelta(days=2),
                **multiply_well_planner_step_co2(mocked_well_planner_step_co2, 1 / saved_duration * 0.25),
            ),
            WellPlannerCo2Dataset(
                date=date + timedelta(days=3),
                **multiply_well_planner_step_co2(mocked_well_planner_step_co2, 1 / saved_duration * 0.50),
            ),
        ]

        dataset = get_well_planner_saved_co2_dataset(well_planner=well_planner)

        assert dataset == expected_dataset

    def test_calculate_hourly_saved_co2_dataset(
        self,
        mock_calculate_well_planner_co2_improvement: MagicMock,
        mocked_well_planner_step_co2: WellPlannerStepCO2Result,
    ):
        well_planner = WellPlannerFactory()
        WellPlannerPlannedStepFactory(
            well_planner=well_planner, improved_duration=1.5, duration=1, waiting_on_weather=100
        )
        WellPlannerPlannedStepFactory(
            well_planner=well_planner, improved_duration=1.25, duration=0.75, waiting_on_weather=100
        )
        saved_duration = 0.75

        date = datetime.combine(well_planner.planned_start_date, datetime.min.time()).replace(tzinfo=pytz.UTC)

        expected_dataset = [
            WellPlannerCo2Dataset(
                date=date + timedelta(days=2, hours=22),
                **multiply_well_planner_step_co2(mocked_well_planner_step_co2, 1 / saved_duration / 24),
            ),
            WellPlannerCo2Dataset(
                date=date + timedelta(days=2, hours=23),
                **multiply_well_planner_step_co2(mocked_well_planner_step_co2, 1 / saved_duration / 24),
            ),
            WellPlannerCo2Dataset(
                date=date + timedelta(days=3, hours=0),
                **multiply_well_planner_step_co2(mocked_well_planner_step_co2, 1 / saved_duration / 24),
            ),
            WellPlannerCo2Dataset(
                date=date + timedelta(days=3, hours=1),
                **multiply_well_planner_step_co2(mocked_well_planner_step_co2, 1 / saved_duration / 24),
            ),
            WellPlannerCo2Dataset(
                date=date + timedelta(days=3, hours=2),
                **multiply_well_planner_step_co2(mocked_well_planner_step_co2, 1 / saved_duration / 24),
            ),
        ]

        dataset = get_well_planner_saved_co2_dataset(
            well_planner=well_planner,
            start_date=date + timedelta(days=2, hours=22),
            end_date=date + timedelta(days=3, hours=2),
        )

        assert dataset == expected_dataset


@pytest.mark.django_db
class TestGetWellPlannerSummary:
    def test_should_get_well_planner_summary(
        self,
        mock_calculate_well_planner_step_co2: MagicMock,
        mocked_well_planner_step_co2: MagicMock,
    ):
        well_planner = WellPlannerFactory()
        BaselineInputFactory(baseline__asset=well_planner.asset)
        WellPlannerPlannedStepFactory.create_batch(3, well_planner=well_planner, duration=2, improved_duration=1)

        expected_summary = {
            'total_baseline': mocked_well_planner_step_co2['baseline'] * 3,
            'total_target': mocked_well_planner_step_co2['target'] * 3,
            'total_improved_duration': 3,
        }

        well_planner_summary = get_well_planner_summary(well_planner)
        assert well_planner_summary == expected_summary


@pytest.mark.django_db
class TestCompleteWellPlannerPlanning:
    def test_should_complete_well_planner_planning(self):
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=WellPlannerWizardStep.WELL_PLANNING, actual_start_date=None)
        (
            emission_reduction_initiative_1,
            emission_reduction_initiative_2,
        ) = EmissionReductionInitiativeFactory.create_batch(
            2, emission_management_plan=well_planner.emission_management_plan
        )

        planned_step_1, planned_step_2 = WellPlannerPlannedStepFactory.create_batch(2, well_planner=well_planner)
        planned_step_1.emission_reduction_initiatives.add(emission_reduction_initiative_1)
        planned_step_2.emission_reduction_initiatives.add(emission_reduction_initiative_2)

        planned_helicopter_use = PlannedHelicopterUseFactory(well_planner=well_planner)
        vessel_type = VesselTypeFactory()
        planned_vessel_use_summer = PlannedVesselUseFactory(
            well_planner=well_planner,
            vessel_type=vessel_type,
            duration=5,
            waiting_on_weather=15,
            season=AssetSeason.SUMMER,
        )
        planned_vessel_use_winter = PlannedVesselUseFactory(
            well_planner=well_planner,
            vessel_type=vessel_type,
            duration=3,
            waiting_on_weather=10,
            season=AssetSeason.WINTER,
        )

        completed_well_planner = complete_well_planner_planning(well_planner=well_planner, user=user)

        assert completed_well_planner.current_step == WellPlannerWizardStep.WELL_REVIEWING
        assert completed_well_planner.actual_start_date == well_planner.planned_start_date

        complete_helicopter_use = completed_well_planner.completehelicopteruse_set.get()
        helicopter_use_fields = [
            'helicopter_type',
            'trips',
            'trip_duration',
            'exposure_against_current_well',
            'quota_obligation',
        ]
        for field in helicopter_use_fields:
            assert getattr(complete_helicopter_use, field) == getattr(planned_helicopter_use, field)

        assert complete_helicopter_use.approved is False

        (
            complete_vessel_use_summer,
            complete_vessel_use_winter,
        ) = completed_well_planner.completevesseluse_set.order_by('id')

        vessel_use_fields = [
            'well_planner',
            'vessel_type',
            'season',
            'duration',
            'exposure_against_current_well',
            'waiting_on_weather',
            'quota_obligation',
        ]
        for field in vessel_use_fields:
            assert getattr(complete_vessel_use_summer, field) == getattr(planned_vessel_use_summer, field)
            assert getattr(complete_vessel_use_winter, field) == getattr(planned_vessel_use_winter, field)

        assert complete_vessel_use_summer.approved is False
        assert complete_vessel_use_winter.approved is False

        well_planner_complete_steps = completed_well_planner.complete_steps.order_by('id')
        assert well_planner_complete_steps.count() == 2
        well_planner_complete_step_1, well_planner_complete_step_2 = well_planner_complete_steps

        for field in [
            "phase",
            "mode",
            "season",
            "well_section_length",
            "carbon_capture_storage_system_quantity",
            "waiting_on_weather",
            "comment",
            "external_energy_supply_enabled",
            "external_energy_supply_quota",
        ]:
            assert getattr(well_planner_complete_step_1, field) == getattr(planned_step_1, field)
            assert getattr(well_planner_complete_step_2, field) == getattr(planned_step_2, field)

        assert well_planner_complete_step_1.duration == planned_step_1.improved_duration
        assert list(well_planner_complete_step_1.emission_reduction_initiatives.all()) == [
            emission_reduction_initiative_1
        ]

        assert well_planner_complete_step_2.duration == planned_step_2.improved_duration
        assert list(well_planner_complete_step_2.emission_reduction_initiatives.all()) == [
            emission_reduction_initiative_2
        ]

    @pytest.mark.parametrize(
        "current_step",
        (set(WellPlannerWizardStep.values) - {WellPlannerWizardStep.WELL_PLANNING}),
    )
    def test_should_raise_validation_error_for_invalid_current_step(self, current_step: WellPlannerWizardStep):
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=current_step)
        WellPlannerPlannedStep(well_planner=well_planner)

        with pytest.raises(ValidationError) as ex:
            complete_well_planner_planning(well_planner=well_planner, user=user)

        assert ex.value.message == "Plan cannot be completed right now."

    def test_should_raise_validation_error_for_no_steps(self):
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=WellPlannerWizardStep.WELL_PLANNING)

        with pytest.raises(ValidationError) as ex:
            complete_well_planner_planning(well_planner=well_planner, user=user)

        assert ex.value.message == "At least one phase must be added to complete the plan."


@pytest.mark.django_db
class TestCreateWellPlannerCompleteStep:
    @pytest.mark.parametrize(
        'current_step', (WellPlannerWizardStep.WELL_REVIEWING, WellPlannerWizardStep.WELL_REPORTING)
    )
    def test_should_create_well_planner_complete_step(self, current_step: WellPlannerWizardStep):
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=current_step)
        custom_emission_reduction_initiatives = EmissionReductionInitiativeFactory.create_batch(
            2, emission_management_plan=well_planner.emission_management_plan
        )
        phase = CustomPhaseFactory(asset=well_planner.asset)
        mode = CustomModeFactory(asset=well_planner.asset)
        first_material_type, second_material_type = MaterialTypeFactory.create_batch(
            2, tenant=well_planner.asset.tenant
        )
        materials_data = [
            WellPlannerStepMaterialData(material_type=first_material_type, quantity=10, quota=False),
            WellPlannerStepMaterialData(material_type=second_material_type, quantity=15, quota=True),
        ]
        BaselineInputFactory(
            baseline=well_planner.baseline, phase=phase, mode=mode, season=WELL_PLANNER_COMPLETE_STEP_DATA["season"]
        )

        data = {
            **WELL_PLANNER_COMPLETE_STEP_DATA,
            "phase": phase,
            "mode": mode,
            "well_planner": well_planner,
        }

        complete_step = create_well_planner_complete_step(
            user=user,
            emission_reduction_initiatives=custom_emission_reduction_initiatives,
            materials=materials_data,
            **data,
        )

        assert complete_step.pk is not None
        assert complete_step.approved is False

        for field, value in data.items():
            assert getattr(complete_step, field) == value

        assert list(complete_step.emission_reduction_initiatives.all()) == custom_emission_reduction_initiatives

        well_planner = complete_step.well_planner
        well_planner.refresh_from_db()
        assert well_planner.current_step == WellPlannerWizardStep.WELL_REVIEWING

        for material_data, material in zip(materials_data, complete_step.materials.order_by('pk')):
            for field, value in material_data.items():
                assert getattr(material, field) == value

    @pytest.mark.parametrize(
        'current_step',
        (
            set(WellPlannerWizardStep.values)
            - {WellPlannerWizardStep.WELL_REVIEWING, WellPlannerWizardStep.WELL_REPORTING}
        ),
    )
    def test_should_raise_error_for_invalid_current_step(self, current_step: WellPlannerWizardStep):
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=current_step)
        with pytest.raises(ValidationError) as ex:
            create_well_planner_complete_step(
                well_planner=well_planner,
                user=user,
                emission_reduction_initiatives=[],
                phase=CustomPhaseFactory(asset=well_planner.asset),
                mode=CustomModeFactory(asset=well_planner.asset),
                **WELL_PLANNER_COMPLETE_STEP_DATA,
            )
        assert ex.value.message == "Phase cannot be created right now."

    def test_should_create_well_planner_complete_step_without_optional_parameters(self):
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=WellPlannerWizardStep.WELL_REVIEWING)
        phase = CustomPhaseFactory(asset=well_planner.asset)
        mode = CustomModeFactory(asset=well_planner.asset)
        BaselineInputFactory(
            baseline=well_planner.baseline, phase=phase, mode=mode, season=WELL_PLANNER_COMPLETE_STEP_DATA["season"]
        )
        complete_step = create_well_planner_complete_step(
            well_planner=well_planner,
            user=user,
            phase=phase,
            mode=mode,
            emission_reduction_initiatives=[],
            materials=[],
            **WELL_PLANNER_COMPLETE_STEP_DATA,
        )

        assert complete_step.pk is not None
        assert complete_step.well_planner == well_planner

        for field, value in WELL_PLANNER_COMPLETE_STEP_DATA.items():
            assert getattr(complete_step, field) == value

        assert complete_step.emission_reduction_initiatives.count() == 0

        well_planner = complete_step.well_planner
        well_planner.refresh_from_db()
        assert well_planner.current_step == WellPlannerWizardStep.WELL_REVIEWING


@pytest.mark.django_db
class TestUpdateWellPlannerCompleteStep:
    @pytest.mark.parametrize(
        'current_step', (WellPlannerWizardStep.WELL_REVIEWING, WellPlannerWizardStep.WELL_REPORTING)
    )
    def test_should_update_well_planner_complete_step(self, current_step: WellPlannerWizardStep):
        user = UserFactory()
        asset = AssetFactory()
        complete_step = WellPlannerCompleteStepFactory(
            well_planner__asset=asset, approved=True, well_planner__current_step=current_step
        )
        old_emission_reduction_initiatives = EmissionReductionInitiativeFactory.create_batch(
            2, emission_management_plan=complete_step.well_planner.emission_management_plan
        )
        complete_step.emission_reduction_initiatives.add(*old_emission_reduction_initiatives)

        old_material, _ = WellCompleteStepMaterialFactory.create_batch(2, step=complete_step)
        material_type = MaterialTypeFactory(tenant=asset.tenant)

        materials_data = [
            WellPlannerStepMaterialData(id=old_material.pk, material_type=material_type, quantity=10.0, quota=False),
            WellPlannerStepMaterialData(material_type=old_material.material_type, quantity=99.9, quota=True),
            WellPlannerStepMaterialData(material_type=material_type, quantity=15.0, quota=True),
        ]

        new_emission_reduction_initiatives = EmissionReductionInitiativeFactory.create_batch(
            2, emission_management_plan=complete_step.well_planner.emission_management_plan
        )
        phase = CustomPhaseFactory(asset=asset)
        mode = CustomModeFactory(asset=asset)
        BaselineInputFactory(
            baseline=complete_step.well_planner.baseline,
            phase=phase,
            mode=mode,
            season=WELL_PLANNER_COMPLETE_STEP_DATA["season"],
        )

        data = {
            **WELL_PLANNER_COMPLETE_STEP_DATA,
            "phase": phase,
            "mode": mode,
        }

        updated_complete_step = update_well_planner_complete_step(
            complete_step=complete_step,
            user=user,
            emission_reduction_initiatives=new_emission_reduction_initiatives,
            materials=materials_data,
            **data,
        )

        assert updated_complete_step.pk == complete_step.pk
        assert updated_complete_step.well_planner == complete_step.well_planner
        assert updated_complete_step.approved is False

        for field, value in data.items():
            assert getattr(updated_complete_step, field) == value

        assert list(updated_complete_step.emission_reduction_initiatives.all()) == new_emission_reduction_initiatives

        for material_data, material in zip(materials_data, updated_complete_step.materials.order_by('pk')):
            for field, value in material_data.items():
                assert getattr(material, field) == value

        well_planner = complete_step.well_planner
        well_planner.refresh_from_db()
        assert well_planner.current_step == WellPlannerWizardStep.WELL_REVIEWING

    @pytest.mark.parametrize(
        'current_step',
        (
            set(WellPlannerWizardStep.values)
            - {WellPlannerWizardStep.WELL_REVIEWING, WellPlannerWizardStep.WELL_REPORTING}
        ),
    )
    def test_should_raise_error_for_invalid_current_step(self, current_step: WellPlannerWizardStep):
        user = UserFactory()
        asset = AssetFactory()
        complete_step = WellPlannerCompleteStepFactory(
            well_planner__asset=asset, approved=True, well_planner__current_step=current_step
        )

        with pytest.raises(ValidationError) as ex:
            update_well_planner_complete_step(
                complete_step=complete_step,
                user=user,
                emission_reduction_initiatives=[],
                phase=CustomPhaseFactory(asset=asset),
                mode=CustomModeFactory(asset=asset),
                **WELL_PLANNER_COMPLETE_STEP_DATA,
            )

        assert ex.value.message == "Phase cannot be updated right now."

    def test_should_update_well_planner_complete_step_without_optional_data(self):
        user = UserFactory()
        asset = AssetFactory()
        complete_step = WellPlannerCompleteStepFactory(
            well_planner__asset=asset,
            approved=True,
            well_planner__current_step=WellPlannerWizardStep.WELL_REVIEWING,
        )
        phase = CustomPhaseFactory(asset=asset)
        mode = CustomModeFactory(asset=asset)
        BaselineInputFactory(
            baseline=complete_step.well_planner.baseline,
            phase=phase,
            mode=mode,
            season=WELL_PLANNER_COMPLETE_STEP_DATA["season"],
        )
        old_emission_reduction_initiatives = EmissionReductionInitiativeFactory.create_batch(
            2, emission_management_plan=complete_step.well_planner.emission_management_plan
        )
        complete_step.emission_reduction_initiatives.add(*old_emission_reduction_initiatives)

        updated_complete_step = update_well_planner_complete_step(
            complete_step=complete_step,
            user=user,
            phase=phase,
            mode=mode,
            emission_reduction_initiatives=[],
            materials=[],
            **WELL_PLANNER_COMPLETE_STEP_DATA,
        )

        assert updated_complete_step.pk == complete_step.pk
        assert updated_complete_step.well_planner == complete_step.well_planner
        assert updated_complete_step.approved is False

        for field, value in WELL_PLANNER_COMPLETE_STEP_DATA.items():
            assert getattr(updated_complete_step, field) == value

        assert updated_complete_step.emission_reduction_initiatives.count() == 0

        well_planner = complete_step.well_planner
        well_planner.refresh_from_db()
        assert well_planner.current_step == WellPlannerWizardStep.WELL_REVIEWING


@pytest.mark.django_db
class TestDeleteWellPlannerCompleteStep:
    @pytest.mark.parametrize(
        'current_step', (WellPlannerWizardStep.WELL_REVIEWING, WellPlannerWizardStep.WELL_REPORTING)
    )
    def test_should_delete_well_planner_planned_step(self, current_step: WellPlannerWizardStep):
        user = UserFactory()
        complete_step = WellPlannerCompleteStepFactory(well_planner__current_step=current_step)

        delete_well_planner_complete_step(complete_step=complete_step, user=user)

        assert not WellPlannerCompleteStep.objects.filter(pk=complete_step.pk).exists()
        well_planner = complete_step.well_planner
        well_planner.refresh_from_db()
        assert well_planner.current_step == WellPlannerWizardStep.WELL_REVIEWING

    @pytest.mark.parametrize(
        'current_step',
        (
            set(WellPlannerWizardStep.values)
            - {WellPlannerWizardStep.WELL_REVIEWING, WellPlannerWizardStep.WELL_REPORTING}
        ),
    )
    def test_should_raise_error_for_invalid_current_step(self, current_step: WellPlannerWizardStep):
        user = UserFactory()
        complete_step = WellPlannerCompleteStepFactory(well_planner__current_step=current_step)

        with pytest.raises(ValidationError) as ex:
            delete_well_planner_complete_step(complete_step=complete_step, user=user)

        assert ex.value.message == "Phase cannot be deleted right now."


@pytest.mark.django_db
class TestCompleteWellPlannerReviewing:
    @pytest.mark.parametrize(
        'current_step', (WellPlannerWizardStep.WELL_REVIEWING, WellPlannerWizardStep.WELL_REPORTING)
    )
    def test_should_complete_well_planner_reviewing(self, current_step: WellPlannerWizardStep):
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=current_step)
        WellPlannerCompleteStepFactory.create_batch(2, well_planner=well_planner, approved=True)
        CompleteHelicopterUseFactory(well_planner=well_planner, approved=True)
        CompleteVesselUseFactory(well_planner=well_planner, approved=True)

        completed_well_planner = complete_well_planner_reviewing(well_planner=well_planner, user=user)

        assert completed_well_planner.current_step == WellPlannerWizardStep.WELL_REPORTING

    def test_should_raise_validation_error_for_no_steps(self):
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=WellPlannerWizardStep.WELL_REVIEWING)

        with pytest.raises(ValidationError) as excinfo:
            complete_well_planner_reviewing(well_planner=well_planner, user=user)

        assert excinfo.value.message == "At least one phase must be added to complete the plan."

    def test_should_raise_validation_error_for_unapproved_steps(self):
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=WellPlannerWizardStep.WELL_REVIEWING)
        WellPlannerCompleteStepFactory(well_planner=well_planner, approved=True)
        WellPlannerCompleteStepFactory(well_planner=well_planner, approved=False)
        CompleteHelicopterUseFactory(well_planner=well_planner, approved=True)
        CompleteVesselUseFactory(well_planner=well_planner, approved=True)

        with pytest.raises(ValidationError) as ex:
            complete_well_planner_reviewing(well_planner=well_planner, user=user)

        assert ex.value.message == "All phases must be approved to complete the review."

    def test_should_raise_validation_error_for_unapproved_vessels(self):
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=WellPlannerWizardStep.WELL_REVIEWING)
        WellPlannerCompleteStepFactory(well_planner=well_planner, approved=True)
        CompleteHelicopterUseFactory(well_planner=well_planner, approved=True)
        CompleteVesselUseFactory(well_planner=well_planner, approved=False)

        with pytest.raises(ValidationError) as ex:
            complete_well_planner_reviewing(well_planner=well_planner, user=user)

        assert ex.value.message == "All vessels must be approved to complete the review."

    def test_should_raise_validation_error_for_unapproved_helicopters(self):
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=WellPlannerWizardStep.WELL_REVIEWING)
        WellPlannerCompleteStepFactory(well_planner=well_planner, approved=True)
        CompleteHelicopterUseFactory(well_planner=well_planner, approved=False)
        CompleteVesselUseFactory(well_planner=well_planner, approved=True)

        with pytest.raises(ValidationError) as ex:
            complete_well_planner_reviewing(well_planner=well_planner, user=user)

        assert ex.value.message == "All helicopters must be approved to complete the review."

    def test_should_raise_validation_error_for_invalid_current_step(self):
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=WellPlannerWizardStep.WELL_PLANNING)
        WellPlannerCompleteStepFactory(well_planner=well_planner, approved=True)
        CompleteHelicopterUseFactory(well_planner=well_planner, approved=False)
        CompleteVesselUseFactory(well_planner=well_planner, approved=False)

        with pytest.raises(ValidationError) as ex:
            complete_well_planner_reviewing(well_planner=well_planner, user=user)

        assert ex.value.message == "Plan cannot be completed right now."


@pytest.mark.django_db
class TestApproveWellPlannerCompleteSteps:
    @pytest.mark.parametrize(
        'current_step', (WellPlannerWizardStep.WELL_REVIEWING, WellPlannerWizardStep.WELL_REPORTING)
    )
    def test_should_approve_well_planner_complete_steps(self, current_step: WellPlannerWizardStep):
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=current_step)
        first_complete_step = WellPlannerCompleteStepFactory(well_planner=well_planner, approved=False)
        second_complete_step = WellPlannerCompleteStepFactory(well_planner=well_planner, approved=True)
        complete_steps = [first_complete_step, second_complete_step]

        approve_well_planner_complete_steps(user=user, well_planner=well_planner, complete_steps=complete_steps)

        for complete_step in complete_steps:
            complete_step.refresh_from_db()

            assert complete_step.approved is True

    @pytest.mark.parametrize(
        'current_step',
        set(WellPlannerWizardStep.values)
        - {WellPlannerWizardStep.WELL_REVIEWING, WellPlannerWizardStep.WELL_REPORTING},
    )
    def test_raise_for_invalid_current_step(self, current_step: WellPlannerWizardStep):
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=current_step)
        complete_step = WellPlannerCompleteStepFactory(well_planner=well_planner)

        with pytest.raises(ValidationError) as ex:
            approve_well_planner_complete_steps(user=user, well_planner=well_planner, complete_steps=[complete_step])

        assert ex.value.message == "Phases cannot be approved right now."

    def test_raise_for_invalid_well_plan(self):
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=WellPlannerWizardStep.WELL_REVIEWING)
        complete_step = WellPlannerCompleteStepFactory()

        with pytest.raises(ValidationError) as ex:
            approve_well_planner_complete_steps(user=user, well_planner=well_planner, complete_steps=[complete_step])

        assert ex.value.message_dict == {"steps": [f'Phase "{complete_step.pk}" doesn\'t exist.']}

    @pytest.mark.parametrize(
        'current_step',
        (
            set(WellPlannerWizardStep.values)
            - {WellPlannerWizardStep.WELL_REVIEWING, WellPlannerWizardStep.WELL_REPORTING}
        ),
    )
    def test_should_raise_error_for_invalid_current_step(self, current_step: WellPlannerWizardStep):
        user = UserFactory()
        complete_step = WellPlannerCompleteStepFactory(approved=False, well_planner__current_step=current_step)

        with pytest.raises(ValidationError) as ex:
            approve_well_planner_complete_steps(
                well_planner=complete_step.well_planner, complete_steps=[complete_step], user=user
            )

        assert ex.value.message == "Phases cannot be approved right now."


@pytest.mark.django_db
def test_get_well_planner_daily_measured_co2_dataset(
    mock_calculate_measured_well_planner_step_co2: MagicMock,
    mocked_well_planner_step_co2: WellPlannerStepCO2Result,
):
    complete_step = WellPlannerCompleteStepFactory(duration=0.5)

    assert get_well_planner_daily_measured_co2_dataset(
        complete_step=complete_step,
        plan_start_date=datetime(2022, 6, 1, 0),
        plan_duration=6.5,
        season_duration=4.5,
        step_waiting_duration=3.75,
        step_duration=0.5,
    ) == [
        WellPlannerStepCo2Dataset(date=datetime(2022, 6, 4, 0), step=complete_step, **mocked_well_planner_step_co2),
        WellPlannerStepCo2Dataset(date=datetime(2022, 6, 5, 0), step=complete_step, **mocked_well_planner_step_co2),
    ]

    assert mock_calculate_measured_well_planner_step_co2.call_args_list == [
        call(
            complete_step=complete_step,
            start=datetime(2022, 6, 4, 18, 0),
            end=datetime(2022, 6, 5, 0, 0),
            total_duration=6.5,
            total_season_duration=4.5,
        ),
        call(
            complete_step=complete_step,
            start=datetime(2022, 6, 5, 0, 0),
            end=datetime(2022, 6, 5, 6, 0),
            total_duration=6.5,
            total_season_duration=4.5,
        ),
    ]


@pytest.mark.django_db
class TestGetWellPlannerDailyMeasuredCo2Dataset:
    def test_filter_co2_dataset_by_start_end_dates(
        self,
        mock_calculate_measured_well_planner_step_co2: MagicMock,
        mocked_well_planner_step_co2: WellPlannerStepCO2Result,
    ):
        complete_step = WellPlannerCompleteStepFactory(duration=1.5)
        start_date = datetime(2022, 6, 5, 1, 0)
        end_date = datetime(2022, 6, 5, 3, 0)

        assert get_well_planner_hourly_measured_co2_dataset(
            start_date=start_date,
            end_date=end_date,
            complete_step=complete_step,
            plan_start_date=datetime(2022, 6, 1, 0),
            plan_duration=6.5,
            season_duration=4.5,
            step_waiting_duration=3.75,
            step_duration=1.5,
        ) == [
            WellPlannerStepCo2Dataset(
                date=datetime(2022, 6, 5, 1, 0), step=complete_step, **mocked_well_planner_step_co2
            ),
            WellPlannerStepCo2Dataset(
                date=datetime(2022, 6, 5, 2, 0), step=complete_step, **mocked_well_planner_step_co2
            ),
            WellPlannerStepCo2Dataset(
                date=datetime(2022, 6, 5, 3, 0), step=complete_step, **mocked_well_planner_step_co2
            ),
        ]

        assert mock_calculate_measured_well_planner_step_co2.call_args_list == [
            call(
                complete_step=complete_step,
                start=datetime(2022, 6, 5, 1, 0),
                end=datetime(2022, 6, 5, 2, 0),
                total_duration=6.5,
                total_season_duration=4.5,
            ),
            call(
                complete_step=complete_step,
                start=datetime(2022, 6, 5, 2, 0),
                end=datetime(2022, 6, 5, 3, 0),
                total_duration=6.5,
                total_season_duration=4.5,
            ),
            call(
                complete_step=complete_step,
                start=datetime(2022, 6, 5, 3, 0),
                end=datetime(2022, 6, 5, 4, 0),
                total_duration=6.5,
                total_season_duration=4.5,
            ),
        ]

    @pytest.mark.parametrize(
        'plan_start_date, step_duration, step_waiting_duration',
        (
            (datetime(2022, 5, 1, 0), 10, 20),
            (datetime(2022, 6, 1, 0), 10, 20),
        ),
    )
    def test_step_outside_start_end_dates(
        self,
        plan_start_date: datetime,
        step_duration: float,
        step_waiting_duration: float,
        mock_calculate_measured_well_planner_step_co2: MagicMock,
    ):
        complete_step = WellPlannerCompleteStepFactory(duration=1.5)
        start_date = datetime(2022, 6, 4, 0, 0)
        end_date = datetime(2022, 6, 6, 0, 0)

        assert (
            get_well_planner_hourly_measured_co2_dataset(
                start_date=start_date,
                end_date=end_date,
                complete_step=complete_step,
                plan_start_date=plan_start_date,
                step_duration=step_duration,
                step_waiting_duration=step_waiting_duration,
                plan_duration=6.5,
                season_duration=4.5,
            )
            == []
        )

        assert mock_calculate_measured_well_planner_step_co2.call_args_list == []


@pytest.mark.django_db
class TestGetWellPlannerMeasuredCo2Dataset:
    def test_should_get_well_planner_daily_measured_co2_dataset(
        self,
        mock_calculate_measured_well_planner_step_co2: MagicMock,
        mocked_well_planner_step_co2: WellPlannerStepCO2Result,
    ):
        well_planner = WellPlannerFactory(current_step=WellPlannerWizardStep.WELL_REVIEWING)
        complete_step_1 = WellPlannerCompleteStepFactory(well_planner=well_planner, duration=0.5)
        complete_step_2 = WellPlannerCompleteStepFactory(well_planner=well_planner, duration=0.25)
        complete_step_3 = WellPlannerCompleteStepFactory(well_planner=well_planner, duration=0.25)
        complete_step_4 = WellPlannerCompleteStepFactory(well_planner=well_planner, duration=1.25)
        complete_step_5 = WellPlannerCompleteStepFactory(well_planner=well_planner, duration=1)

        date = datetime.combine(well_planner.actual_start_date, datetime.min.time())

        expected_dataset = [
            WellPlannerStepCo2Dataset(date=date, step=complete_step_1, **mocked_well_planner_step_co2),
            WellPlannerStepCo2Dataset(date=date, step=complete_step_2, **mocked_well_planner_step_co2),
            WellPlannerStepCo2Dataset(date=date, step=complete_step_3, **mocked_well_planner_step_co2),
            WellPlannerStepCo2Dataset(
                date=date + timedelta(days=1),
                step=complete_step_4,
                **mocked_well_planner_step_co2,
            ),
            WellPlannerStepCo2Dataset(
                date=date + timedelta(days=2),
                step=complete_step_4,
                **mocked_well_planner_step_co2,
            ),
            WellPlannerStepCo2Dataset(
                date=date + timedelta(days=2),
                step=complete_step_5,
                **mocked_well_planner_step_co2,
            ),
            WellPlannerStepCo2Dataset(
                date=date + timedelta(days=3),
                step=complete_step_5,
                **mocked_well_planner_step_co2,
            ),
        ]

        dataset = get_well_planner_measured_co2_dataset(well_planner=well_planner)

        assert dataset == expected_dataset

    def test_should_get_well_planner_hourly_measured_co2_dataset(
        self,
        mock_calculate_measured_well_planner_step_co2: MagicMock,
        mocked_well_planner_step_co2: WellPlannerStepCO2Result,
    ):
        well_planner = WellPlannerFactory(current_step=WellPlannerWizardStep.WELL_REVIEWING)
        WellPlannerCompleteStepFactory(well_planner=well_planner, duration=0.5)
        WellPlannerCompleteStepFactory(well_planner=well_planner, duration=0.25)
        complete_step_3 = WellPlannerCompleteStepFactory(well_planner=well_planner, duration=0.25)
        complete_step_4 = WellPlannerCompleteStepFactory(well_planner=well_planner, duration=1.25)
        WellPlannerCompleteStepFactory(well_planner=well_planner, duration=1)

        date = datetime.combine(well_planner.actual_start_date, datetime.min.time()).replace(tzinfo=pytz.UTC)

        expected_dataset = [
            WellPlannerStepCo2Dataset(
                date=date + timedelta(days=0, hours=22), step=complete_step_3, **mocked_well_planner_step_co2
            ),
            WellPlannerStepCo2Dataset(
                date=date + timedelta(days=0, hours=23), step=complete_step_3, **mocked_well_planner_step_co2
            ),
            WellPlannerStepCo2Dataset(
                date=date + timedelta(days=1, hours=0), step=complete_step_4, **mocked_well_planner_step_co2
            ),
            WellPlannerStepCo2Dataset(
                date=date + timedelta(days=1, hours=1), step=complete_step_4, **mocked_well_planner_step_co2
            ),
            WellPlannerStepCo2Dataset(
                date=date + timedelta(days=1, hours=2), step=complete_step_4, **mocked_well_planner_step_co2
            ),
        ]

        dataset = get_well_planner_measured_co2_dataset(
            well_planner=well_planner,
            start_date=date + timedelta(days=0, hours=22),
            end_date=date + timedelta(days=1, hours=2),
        )

        assert dataset == expected_dataset


@pytest.mark.django_db
@pytest.mark.parametrize(
    "monitor_function_type",
    (
        MonitorFunctionType.WIND_SPEED,
        MonitorFunctionType.AIR_TEMPERATURE,
        MonitorFunctionType.WAVE_HEAVE,
    ),
)
class TestGetWellPlannerMeasurementDataset:
    @pytest.fixture()
    def setup_monitor_function(self, monitor_function_type: MonitorFunctionType):
        self.well_planner = WellPlannerFactory(current_step=WellPlannerWizardStep.WELL_REVIEWING)
        WellPlannerCompleteStepFactory(well_planner=self.well_planner, duration=3)

        start_datetime = datetime(
            year=self.well_planner.actual_start_date.year,
            month=self.well_planner.actual_start_date.month,
            day=self.well_planner.actual_start_date.day,
        )

        monitor_function = MonitorFunctionFactory(
            vessel=self.well_planner.asset.vessel,
            type=monitor_function_type,
        )

        MonitorFunctionValueFactory(monitor_function=monitor_function, value=1, date=start_datetime)
        MonitorFunctionValueFactory(
            monitor_function=monitor_function, value=2, date=start_datetime + timedelta(hours=1)
        )
        MonitorFunctionValueFactory(
            monitor_function=monitor_function, value=3, date=start_datetime + timedelta(hours=2)
        )
        MonitorFunctionValueFactory(value=3, date=start_datetime + timedelta(hours=2))
        MonitorFunctionValueFactory(monitor_function=monitor_function, value=4, date=start_datetime + timedelta(days=1))
        MonitorFunctionValueFactory(
            monitor_function=monitor_function, value=5, date=start_datetime + timedelta(days=1, hours=22)
        )
        MonitorFunctionValueFactory(
            monitor_function=monitor_function, value=6, date=start_datetime + timedelta(days=1, hours=23)
        )
        MonitorFunctionValueFactory(monitor_function=monitor_function, value=7, date=start_datetime + timedelta(days=2))
        MonitorFunctionValueFactory(
            monitor_function=monitor_function, value=8, date=start_datetime + timedelta(days=2, hours=1)
        )
        MonitorFunctionValueFactory(
            monitor_function=monitor_function, value=9, date=start_datetime + timedelta(days=2, hours=2)
        )
        MonitorFunctionValueFactory(value=3, date=start_datetime + timedelta(days=1, hours=2))

    def test_should_get_well_planner_measurement_daily_dataset(
        self, setup_monitor_function: None, monitor_function_type: MonitorFunctionType
    ):
        date = datetime.combine(self.well_planner.actual_start_date, datetime.min.time()).replace(tzinfo=pytz.UTC)
        expected_dataset = [
            WellPlannerMeasurementDataset(date=date, value=2.0),
            WellPlannerMeasurementDataset(date=date + timedelta(days=1), value=5.0),
            WellPlannerMeasurementDataset(date=date + timedelta(days=2), value=8.0),
        ]

        dataset = get_well_planner_measurement_dataset(
            well_planner=self.well_planner, monitor_function_type=monitor_function_type
        )
        assert dataset == expected_dataset

    def test_should_get_well_planner_measurement_hourly_dataset(
        self, setup_monitor_function: None, monitor_function_type: MonitorFunctionType
    ):
        date = datetime.combine(self.well_planner.actual_start_date, datetime.min.time()).replace(tzinfo=pytz.UTC)
        expected_dataset = [
            WellPlannerMeasurementDataset(date=date + timedelta(days=1, hours=21), value=0.0),
            WellPlannerMeasurementDataset(date=date + timedelta(days=1, hours=22), value=5.0),
            WellPlannerMeasurementDataset(date=date + timedelta(days=1, hours=23), value=6.0),
            WellPlannerMeasurementDataset(date=date + timedelta(days=2, hours=0), value=7.0),
            WellPlannerMeasurementDataset(date=date + timedelta(days=2, hours=1), value=8.0),
            WellPlannerMeasurementDataset(date=date + timedelta(days=2, hours=2), value=9.0),
        ]

        dataset = get_well_planner_measurement_dataset(
            well_planner=self.well_planner,
            monitor_function_type=monitor_function_type,
            start_date=date + timedelta(days=1, hours=21),
            end_date=date + timedelta(days=2, hours=2),
        )
        assert dataset == expected_dataset

    def test_should_return_empty_dataset_for_no_asset_vessel(self, monitor_function_type: MonitorFunctionType):
        well_planner = WellPlannerFactory(asset__vessel=None, current_step=WellPlannerWizardStep.WELL_REVIEWING)
        WellPlannerCompleteStepFactory(well_planner=well_planner, duration=3)

        dataset = get_well_planner_measurement_dataset(
            well_planner=well_planner, monitor_function_type=monitor_function_type
        )
        assert dataset == []


@pytest.mark.django_db
class TestGetWellPlannerMeasuredSummary:
    def test_should_get_well_planner_measured_summary(
        self,
        mock_calculate_measured_well_planner_step_co2: MagicMock,
        mocked_well_planner_step_co2: MagicMock,
    ):
        well_planner = WellPlannerFactory(current_step=WellPlannerWizardStep.WELL_REVIEWING)
        BaselineInputFactory(baseline__asset=well_planner.asset)
        WellPlannerPlannedStepFactory.create_batch(3, well_planner=well_planner, improved_duration=3)
        WellPlannerCompleteStepFactory.create_batch(3, well_planner=well_planner, duration=2)

        expected_summary = WellPlannerMeasuredSummary(
            total_baseline=mocked_well_planner_step_co2['baseline'] * 3,
            total_target=mocked_well_planner_step_co2['target'] * 3,
            total_duration=6.0,
        )

        well_planner_measured_summary = get_well_planner_measured_summary(well_planner)
        assert well_planner_measured_summary == expected_summary


@pytest.mark.django_db
class TestDuplicateWellPlannerPlannedStep:
    def test_duplicate_well_planner_planned_step(self, mocked_calculate_planned_emissions: MagicMock):
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=WellPlannerWizardStep.WELL_PLANNING)
        ExternalEnergySupplyFactory(asset=well_planner.asset)
        WellPlannerPlannedStepFactory()
        first_planned_step = WellPlannerPlannedStepFactory(well_planner=well_planner)
        second_planned_step = WellPlannerPlannedStepFactory(
            well_planner=well_planner,
            duration=5,
            improved_duration=4.5,
        )
        third_planned_step = WellPlannerPlannedStepFactory(well_planner=well_planner)

        for step in [first_planned_step, second_planned_step, third_planned_step]:
            BaselineInputFactory(baseline=well_planner.baseline, phase=step.phase, mode=step.mode, season=step.season)

        assert first_planned_step.order == 0
        assert second_planned_step.order == 1
        assert third_planned_step.order == 2

        duplicate_step = duplicate_well_planner_planned_step(planned_step=second_planned_step, user=user)

        assert duplicate_step.well_planner == well_planner
        assert duplicate_step.duration == 5
        assert duplicate_step.improved_duration == 4.5

        first_planned_step.refresh_from_db()
        second_planned_step.refresh_from_db()
        third_planned_step.refresh_from_db()

        assert first_planned_step.order == 0
        assert second_planned_step.order == 1
        assert duplicate_step.order == 2
        assert third_planned_step.order == 3

        mocked_calculate_planned_emissions.assert_called_once_with(well_planner)

    @pytest.mark.parametrize('current_step', set(WellPlannerWizardStep.values) - {WellPlannerWizardStep.WELL_PLANNING})
    def test_cannot_duplicate_due_to_invalid_current_step(self, current_step):
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=current_step)
        planned_step = WellPlannerPlannedStepFactory(well_planner=well_planner)

        with pytest.raises(ValidationError) as ex:
            duplicate_well_planner_planned_step(planned_step=planned_step, user=user)

        assert ex.value.message == 'Step cannot be duplicated right now.'


@pytest.mark.django_db
class TestDuplicateWellPlannerCompleteStep:
    @pytest.mark.parametrize(
        'current_step', (WellPlannerWizardStep.WELL_REVIEWING, WellPlannerWizardStep.WELL_REPORTING)
    )
    def test_duplicate_well_planner_complete_step(self, current_step: WellPlannerWizardStep):
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=current_step)
        WellPlannerCompleteStepFactory()
        first_complete_step = WellPlannerCompleteStepFactory(well_planner=well_planner)
        second_complete_step = WellPlannerCompleteStepFactory(
            well_planner=well_planner,
            duration=5,
            approved=True,
        )
        third_complete_step = WellPlannerCompleteStepFactory(well_planner=well_planner)

        assert first_complete_step.order == 0
        assert second_complete_step.order == 1
        assert third_complete_step.order == 2

        duplicate_step = duplicate_well_planner_complete_step(complete_step=second_complete_step, user=user)

        assert duplicate_step.well_planner == well_planner
        assert duplicate_step.duration == 5
        assert duplicate_step.approved is False

        first_complete_step.refresh_from_db()
        second_complete_step.refresh_from_db()
        third_complete_step.refresh_from_db()
        well_planner.refresh_from_db()

        assert well_planner.current_step == WellPlannerWizardStep.WELL_REVIEWING

        assert first_complete_step.order == 0
        assert second_complete_step.order == 1
        assert duplicate_step.order == 2
        assert third_complete_step.order == 3

    @pytest.mark.parametrize(
        'current_step',
        set(WellPlannerWizardStep.values)
        - {WellPlannerWizardStep.WELL_REVIEWING, WellPlannerWizardStep.WELL_REPORTING},
    )
    def test_cannot_duplicate_due_to_invalid_current_step(self, current_step):
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=current_step)
        complete_step = WellPlannerCompleteStepFactory(well_planner=well_planner)

        with pytest.raises(ValidationError) as ex:
            duplicate_well_planner_complete_step(complete_step=complete_step, user=user)

        assert ex.value.message == 'Step cannot be duplicated right now.'


@pytest.mark.django_db
def test_copy_well_planner_step():
    well_planner = WellPlannerFactory()
    emission_reduction_initiative_1, emission_reduction_initiative_2 = EmissionReductionInitiativeFactory.create_batch(
        2, emission_management_plan=well_planner.emission_management_plan
    )
    EmissionReductionInitiativeFactory(emission_management_plan=well_planner.emission_management_plan, deleted=True)

    planned_step = WellPlannerPlannedStepFactory(
        well_planner=well_planner,
        duration=2.5,
        waiting_on_weather=100,
        improved_duration=4.5,
    )
    planned_step.emission_reduction_initiatives.add(*[emission_reduction_initiative_1, emission_reduction_initiative_2])
    materials = [
        WellPlannedStepMaterialFactory(step=planned_step, quantity=9.99, quota=False),
        WellPlannedStepMaterialFactory(step=planned_step, quantity=99.99, quota=True),
    ]
    WellPlannedStepMaterialFactory()

    copied_step = copy_well_planner_step(
        well_planner_step_class=WellPlannerPlannedStep,
        copy_step=planned_step,
        well_planner=well_planner,
        duration=2.5,
        improved_duration=4.5,
    )

    assert copied_step.well_planner == well_planner
    assert copied_step.duration == planned_step.duration
    assert copied_step.waiting_on_weather == planned_step.waiting_on_weather
    assert copied_step.improved_duration == planned_step.improved_duration
    assert copied_step.phase == planned_step.phase
    assert copied_step.mode == planned_step.mode
    assert copied_step.season == planned_step.season
    assert copied_step.external_energy_supply_enabled == planned_step.external_energy_supply_enabled
    assert copied_step.carbon_capture_storage_system_quantity == planned_step.carbon_capture_storage_system_quantity

    assert list(copied_step.emission_reduction_initiatives.order_by('id')) == [
        emission_reduction_initiative_1,
        emission_reduction_initiative_2,
    ]

    for material, copied_material in zip(materials, copied_step.materials.all().order_by('id')):
        for field in ['material_type', 'quantity', 'quota']:
            assert getattr(material, field) == getattr(copied_material, field)


@pytest.mark.django_db
class TestMoveWellPlannerPlannedStep:
    def test_move_well_planner_planned_step(self, mocked_calculate_planned_emissions: MagicMock):
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=WellPlannerWizardStep.WELL_PLANNING)
        ExternalEnergySupplyFactory(asset=well_planner.asset)
        first_step, second_step = WellPlannerPlannedStepFactory.create_batch(2, well_planner=well_planner)
        for step in [first_step, second_step]:
            BaselineInputFactory(baseline=well_planner.baseline, phase=step.phase, mode=step.mode, season=step.season)

        assert first_step.order == 0
        assert second_step.order == 1

        move_well_planner_planned_step(
            user=user,
            step=second_step,
            order=0,
        )

        second_step.refresh_from_db()
        first_step.refresh_from_db()
        assert second_step.order == 0
        assert first_step.order == 1

        mocked_calculate_planned_emissions.assert_called_once_with(well_planner)

    @pytest.mark.parametrize('current_step', set(WellPlannerWizardStep.values) - {WellPlannerWizardStep.WELL_PLANNING})
    def test_cannot_move_for_well_planner_with_invalid_current_step(self, current_step: WellPlannerWizardStep):
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=current_step)
        step = WellPlannerPlannedStepFactory(well_planner=well_planner)

        with pytest.raises(ValidationError) as ex:
            move_well_planner_planned_step(
                user=user,
                step=step,
                order=2,
            )

        assert ex.value.message == "Step cannot be moved right now."


@pytest.mark.django_db
class TestMoveWellPlannerCompleteStep:
    @pytest.mark.parametrize(
        'current_step', (WellPlannerWizardStep.WELL_REVIEWING, WellPlannerWizardStep.WELL_REPORTING)
    )
    def test_move_well_planner_complete_steps(self, current_step: WellPlannerWizardStep):
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=current_step)
        first_step, second_step = WellPlannerCompleteStepFactory.create_batch(
            2, well_planner=well_planner, approved=True
        )

        assert first_step.order == 0
        assert second_step.order == 1

        move_well_planner_complete_step(
            user=user,
            step=second_step,
            order=0,
        )

        well_planner.refresh_from_db()
        assert well_planner.current_step == WellPlannerWizardStep.WELL_REVIEWING

        second_step.refresh_from_db()
        first_step.refresh_from_db()
        assert second_step.order == 0
        assert first_step.order == 1

        assert second_step.approved is False

    @pytest.mark.parametrize(
        'current_step',
        set(WellPlannerWizardStep.values)
        - {WellPlannerWizardStep.WELL_REVIEWING, WellPlannerWizardStep.WELL_REPORTING},
    )
    def test_cannot_move_for_well_planner_with_invalid_current_step(self, current_step: WellPlannerWizardStep):
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=current_step)
        step = WellPlannerCompleteStepFactory(well_planner=well_planner)

        with pytest.raises(ValidationError) as ex:
            move_well_planner_complete_step(
                user=user,
                step=step,
                order=2,
            )

        assert ex.value.message == "Step cannot be moved right now."


@pytest.mark.django_db
class TestUpdateWellPlannerPlannedStepEmissionReductionInitiatives:
    def test_should_update_well_planner_planned_step_emission_reduction_initiatives(
        self, mocked_calculate_planned_emissions: MagicMock
    ):
        well_planner = WellPlannerFactory(current_step=WellPlannerWizardStep.WELL_PLANNING)
        ExternalEnergySupplyFactory(asset=well_planner.asset)
        user = UserFactory()
        planned_step = WellPlannerPlannedStepFactory(well_planner=well_planner, duration=10)
        BaselineInputFactory(
            baseline=well_planner.baseline, phase=planned_step.phase, mode=planned_step.mode, season=planned_step.season
        )
        old_emission_reduction_initiatives = [
            EmissionReductionInitiativeFactory(
                emission_management_plan=well_planner.emission_management_plan,
                type=EmissionReductionInitiativeType.BASELOADS,
            ),
            EmissionReductionInitiativeFactory(
                emission_management_plan=well_planner.emission_management_plan,
                type=EmissionReductionInitiativeType.PRODUCTIVITY,
            ),
        ]
        first_new_emission_reduction_initiative = EmissionReductionInitiativeFactory(
            emission_management_plan=well_planner.emission_management_plan,
            type=EmissionReductionInitiativeType.BASELOADS,
        )
        EmissionReductionInitiativeInputFactory(
            emission_reduction_initiative=first_new_emission_reduction_initiative,
            phase=planned_step.phase,
            mode=planned_step.mode,
            value=10,
        )
        second_new_emission_reduction_initiative = EmissionReductionInitiativeFactory(
            emission_management_plan=well_planner.emission_management_plan,
            type=EmissionReductionInitiativeType.PRODUCTIVITY,
        )
        EmissionReductionInitiativeInputFactory(
            emission_reduction_initiative=second_new_emission_reduction_initiative,
            phase=planned_step.phase,
            mode=planned_step.mode,
            value=10,
        )
        planned_step.emission_reduction_initiatives.add(*old_emission_reduction_initiatives)

        updated_planned_step = update_well_planner_planned_step_emission_reduction_initiatives(
            user=user,
            planned_step=planned_step,
            emission_reduction_initiatives=[
                first_new_emission_reduction_initiative,
                second_new_emission_reduction_initiative,
            ],
        )

        assert list(updated_planned_step.emission_reduction_initiatives.order_by('id')) == [
            first_new_emission_reduction_initiative,
            second_new_emission_reduction_initiative,
        ]
        assert updated_planned_step.improved_duration == planned_step.total_duration * 0.9

        mocked_calculate_planned_emissions.assert_called_once_with(well_planner)

    @pytest.mark.parametrize(
        'current_step', (set(WellPlannerWizardStep.values) - {WellPlannerWizardStep.WELL_PLANNING})
    )
    def test_should_raise_error_for_invalid_current_step(self, current_step: WellPlannerWizardStep):
        well_planner = WellPlannerFactory(current_step=current_step)
        user = UserFactory()
        planned_step = WellPlannerPlannedStepFactory(well_planner=well_planner)

        with pytest.raises(ValidationError) as ex:
            update_well_planner_planned_step_emission_reduction_initiatives(
                user=user, planned_step=planned_step, emission_reduction_initiatives=[]
            )

        assert ex.value.message == "Energy reduction initiatives cannot be updated right now."

    def test_should_remove_all_emission_reduction_initiatives_for_empty_list(self):
        well_planner = WellPlannerFactory(current_step=WellPlannerWizardStep.WELL_PLANNING)
        ExternalEnergySupplyFactory(asset=well_planner.asset)
        user = UserFactory()
        planned_step = WellPlannerPlannedStepFactory(well_planner=well_planner)
        BaselineInputFactory(
            baseline=well_planner.baseline, phase=planned_step.phase, mode=planned_step.mode, season=planned_step.season
        )
        old_emission_reduction_initiatives = EmissionReductionInitiativeFactory.create_batch(
            2,
            emission_management_plan=well_planner.emission_management_plan,
        )
        planned_step.emission_reduction_initiatives.add(*old_emission_reduction_initiatives)

        updated_planned_step = update_well_planner_planned_step_emission_reduction_initiatives(
            user=user, planned_step=planned_step, emission_reduction_initiatives=[]
        )

        assert list(updated_planned_step.emission_reduction_initiatives.all()) == []

    def test_should_raise_for_different_asset(self):
        well_planner = WellPlannerFactory(current_step=WellPlannerWizardStep.WELL_PLANNING)
        user = UserFactory()
        planned_step = WellPlannerPlannedStepFactory(well_planner=well_planner)
        BaselineInputFactory(
            baseline=well_planner.baseline, phase=planned_step.phase, mode=planned_step.mode, season=planned_step.season
        )
        old_emission_reduction_initiatives = EmissionReductionInitiativeFactory.create_batch(
            2,
            emission_management_plan=well_planner.emission_management_plan,
        )
        new_emission_reduction_initiatives = EmissionReductionInitiativeFactory.create_batch(2)
        planned_step.emission_reduction_initiatives.add(*old_emission_reduction_initiatives)

        with pytest.raises(ValidationError) as ex:
            update_well_planner_planned_step_emission_reduction_initiatives(
                user=user, planned_step=planned_step, emission_reduction_initiatives=new_emission_reduction_initiatives
            )

        assert ex.value.message_dict == {
            "emission_reduction_initiatives": ["Chosen energy reduction initiative is not a valid choice."]
        }


@pytest.mark.django_db
class TestUpdateWellPlannerCompleteStepEmissionReductionInitiatives:
    @pytest.mark.parametrize(
        'current_step', (WellPlannerWizardStep.WELL_REVIEWING, WellPlannerWizardStep.WELL_REPORTING)
    )
    def test_should_update_well_planner_complete_step_emission_reduction_initiatives(
        self, current_step: WellPlannerWizardStep
    ):
        well_planner = WellPlannerFactory(current_step=current_step)
        user = UserFactory()
        complete_step = WellPlannerCompleteStepFactory(well_planner=well_planner, approved=True)
        BaselineInputFactory(
            baseline=well_planner.baseline,
            phase=complete_step.phase,
            mode=complete_step.mode,
            season=complete_step.season,
        )
        old_emission_reduction_initiatives = EmissionReductionInitiativeFactory.create_batch(
            2,
            emission_management_plan=well_planner.emission_management_plan,
        )
        new_emission_reduction_initiatives = EmissionReductionInitiativeFactory.create_batch(
            2,
            emission_management_plan=well_planner.emission_management_plan,
        )
        complete_step.emission_reduction_initiatives.add(*old_emission_reduction_initiatives)

        updated_complete_step = update_well_planner_complete_step_emission_reduction_initiatives(
            user=user, complete_step=complete_step, emission_reduction_initiatives=new_emission_reduction_initiatives
        )
        assert updated_complete_step.approved is False
        assert updated_complete_step.well_planner.current_step == WellPlannerWizardStep.WELL_REVIEWING
        assert list(updated_complete_step.emission_reduction_initiatives.order_by('id')) == list(
            new_emission_reduction_initiatives
        )

    @pytest.mark.parametrize(
        'current_step',
        (
            set(WellPlannerWizardStep.values)
            - {WellPlannerWizardStep.WELL_REVIEWING, WellPlannerWizardStep.WELL_REPORTING}
        ),
    )
    def test_should_raise_error_for_invalid_current_step(self, current_step: WellPlannerWizardStep):
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=current_step)
        complete_step = WellPlannerCompleteStepFactory(well_planner=well_planner, approved=True)

        with pytest.raises(ValidationError) as ex:
            update_well_planner_complete_step_emission_reduction_initiatives(
                user=user, complete_step=complete_step, emission_reduction_initiatives=[]
            )

        assert ex.value.message == "Energy reduction initiatives cannot be updated right now."

    def test_should_remove_all_emission_reduction_initiatives_for_empty_list(self):
        well_planner = WellPlannerFactory(current_step=WellPlannerWizardStep.WELL_REVIEWING)
        user = UserFactory()
        complete_step = WellPlannerCompleteStepFactory(well_planner=well_planner, approved=True)
        BaselineInputFactory(
            baseline=well_planner.baseline,
            phase=complete_step.phase,
            mode=complete_step.mode,
            season=complete_step.season,
        )
        old_emission_reduction_initiatives = EmissionReductionInitiativeFactory.create_batch(
            2,
            emission_management_plan=well_planner.emission_management_plan,
        )
        complete_step.emission_reduction_initiatives.add(*old_emission_reduction_initiatives)

        updated_complete_step = update_well_planner_complete_step_emission_reduction_initiatives(
            user=user, complete_step=complete_step, emission_reduction_initiatives=[]
        )

        assert updated_complete_step.approved is False
        assert updated_complete_step.well_planner.current_step == WellPlannerWizardStep.WELL_REVIEWING
        assert list(updated_complete_step.emission_reduction_initiatives.all()) == []

    def test_should_raise_for_different_asset(self):
        well_planner = WellPlannerFactory(current_step=WellPlannerWizardStep.WELL_REVIEWING)
        user = UserFactory()
        complete_step = WellPlannerCompleteStepFactory(well_planner=well_planner, approved=True)
        BaselineInputFactory(
            baseline=well_planner.baseline,
            phase=complete_step.phase,
            mode=complete_step.mode,
            season=complete_step.season,
        )
        old_emission_reduction_initiatives = EmissionReductionInitiativeFactory.create_batch(
            2,
            emission_management_plan=well_planner.emission_management_plan,
        )
        new_emission_reduction_initiatives = EmissionReductionInitiativeFactory.create_batch(2)
        complete_step.emission_reduction_initiatives.add(*old_emission_reduction_initiatives)

        with pytest.raises(ValidationError) as ex:
            update_well_planner_complete_step_emission_reduction_initiatives(
                user=user,
                complete_step=complete_step,
                emission_reduction_initiatives=new_emission_reduction_initiatives,
            )

        assert ex.value.message_dict == {
            "emission_reduction_initiatives": ["Chosen energy reduction initiative is not a valid choice."]
        }


@pytest.mark.django_db
class TestApproveWellPlannerCompleteHelicopterUses:
    def test_should_approve_well_planner_complete_helicopter_uses(self):
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=WellPlannerWizardStep.WELL_REVIEWING)
        complete_helicopter_uses = CompleteHelicopterUseFactory.create_batch(
            2, approved=False, well_planner=well_planner
        )
        approved_complete_helicopter_uses = approve_well_planner_complete_helicopter_uses(
            user=user, well_planner=well_planner, complete_helicopter_uses=complete_helicopter_uses
        )

        assert len(approved_complete_helicopter_uses) == len(complete_helicopter_uses)
        assert all(
            approved_complete_helicopter_use.approved
            for approved_complete_helicopter_use in approved_complete_helicopter_uses
        )

    def test_should_raise_for_different_well_planner(self):
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=WellPlannerWizardStep.WELL_REVIEWING)
        complete_helicopter_uses = [
            CompleteHelicopterUseFactory(well_planner=well_planner),
            CompleteHelicopterUseFactory(),
        ]

        with pytest.raises(ValidationError) as ex:
            approve_well_planner_complete_helicopter_uses(
                user=user, well_planner=well_planner, complete_helicopter_uses=complete_helicopter_uses
            )

        assert ex.value.messages == ["Chosen helicopter is not a valid choice."]


@pytest.mark.django_db
class TestApproveWellPlannerCompleteVesselUses:
    def test_should_approve_well_planner_complete_vessel_uses(self):
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=WellPlannerWizardStep.WELL_REVIEWING)
        complete_vessel_uses = CompleteVesselUseFactory.create_batch(2, approved=False, well_planner=well_planner)
        approved_complete_vessel_uses = approve_well_planner_complete_vessel_uses(
            user=user, well_planner=well_planner, complete_vessel_uses=complete_vessel_uses
        )

        assert len(approved_complete_vessel_uses) == len(complete_vessel_uses)
        assert all(
            approved_complete_vessel_use.approved for approved_complete_vessel_use in approved_complete_vessel_uses
        )

    def test_should_raise_for_different_well_planner(self):
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=WellPlannerWizardStep.WELL_REVIEWING)
        complete_vessel_uses = [
            CompleteVesselUseFactory(well_planner=well_planner),
            CompleteVesselUseFactory(),
        ]

        with pytest.raises(ValidationError) as ex:
            approve_well_planner_complete_vessel_uses(
                user=user, well_planner=well_planner, complete_vessel_uses=complete_vessel_uses
            )

        assert ex.value.messages == ["Chosen vessel is not a valid choice."]


@pytest.mark.django_db
class TestSplitDurationIntoHours:
    def test_full_day(self):
        start_time = datetime(year=2022, month=6, day=1, hour=0, minute=0)
        assert list(split_duration_into_hours(start_date=start_time, duration=1)) == [  # 24 hours
            DurationHoursResult(
                hour=datetime(2022, 6, 1, 0, 0),
                duration=1,
                start=datetime(2022, 6, 1, 0, 0),
                end=datetime(2022, 6, 1, 1, 0),
            ),
            DurationHoursResult(
                hour=datetime(2022, 6, 1, 1, 0),
                duration=1,
                start=datetime(2022, 6, 1, 1, 0),
                end=datetime(2022, 6, 1, 2, 0),
            ),
            DurationHoursResult(
                hour=datetime(2022, 6, 1, 2, 0),
                duration=1,
                start=datetime(2022, 6, 1, 2, 0),
                end=datetime(2022, 6, 1, 3, 0),
            ),
            DurationHoursResult(
                hour=datetime(2022, 6, 1, 3, 0),
                duration=1,
                start=datetime(2022, 6, 1, 3, 0),
                end=datetime(2022, 6, 1, 4, 0),
            ),
            DurationHoursResult(
                hour=datetime(2022, 6, 1, 4, 0),
                duration=1,
                start=datetime(2022, 6, 1, 4, 0),
                end=datetime(2022, 6, 1, 5, 0),
            ),
            DurationHoursResult(
                hour=datetime(2022, 6, 1, 5, 0),
                duration=1,
                start=datetime(2022, 6, 1, 5, 0),
                end=datetime(2022, 6, 1, 6, 0),
            ),
            DurationHoursResult(
                hour=datetime(2022, 6, 1, 6, 0),
                duration=1,
                start=datetime(2022, 6, 1, 6, 0),
                end=datetime(2022, 6, 1, 7, 0),
            ),
            DurationHoursResult(
                hour=datetime(2022, 6, 1, 7, 0),
                duration=1,
                start=datetime(2022, 6, 1, 7, 0),
                end=datetime(2022, 6, 1, 8, 0),
            ),
            DurationHoursResult(
                hour=datetime(2022, 6, 1, 8, 0),
                duration=1,
                start=datetime(2022, 6, 1, 8, 0),
                end=datetime(2022, 6, 1, 9, 0),
            ),
            DurationHoursResult(
                hour=datetime(2022, 6, 1, 9, 0),
                duration=1,
                start=datetime(2022, 6, 1, 9, 0),
                end=datetime(2022, 6, 1, 10, 0),
            ),
            DurationHoursResult(
                hour=datetime(2022, 6, 1, 10, 0),
                duration=1,
                start=datetime(2022, 6, 1, 10, 0),
                end=datetime(2022, 6, 1, 11, 0),
            ),
            DurationHoursResult(
                hour=datetime(2022, 6, 1, 11, 0),
                duration=1,
                start=datetime(2022, 6, 1, 11, 0),
                end=datetime(2022, 6, 1, 12, 0),
            ),
            DurationHoursResult(
                hour=datetime(2022, 6, 1, 12, 0),
                duration=1,
                start=datetime(2022, 6, 1, 12, 0),
                end=datetime(2022, 6, 1, 13, 0),
            ),
            DurationHoursResult(
                hour=datetime(2022, 6, 1, 13, 0),
                duration=1,
                start=datetime(2022, 6, 1, 13, 0),
                end=datetime(2022, 6, 1, 14, 0),
            ),
            DurationHoursResult(
                hour=datetime(2022, 6, 1, 14, 0),
                duration=1,
                start=datetime(2022, 6, 1, 14, 0),
                end=datetime(2022, 6, 1, 15, 0),
            ),
            DurationHoursResult(
                hour=datetime(2022, 6, 1, 15, 0),
                duration=1,
                start=datetime(2022, 6, 1, 15, 0),
                end=datetime(2022, 6, 1, 16, 0),
            ),
            DurationHoursResult(
                hour=datetime(2022, 6, 1, 16, 0),
                duration=1,
                start=datetime(2022, 6, 1, 16, 0),
                end=datetime(2022, 6, 1, 17, 0),
            ),
            DurationHoursResult(
                hour=datetime(2022, 6, 1, 17, 0),
                duration=1,
                start=datetime(2022, 6, 1, 17, 0),
                end=datetime(2022, 6, 1, 18, 0),
            ),
            DurationHoursResult(
                hour=datetime(2022, 6, 1, 18, 0),
                duration=1,
                start=datetime(2022, 6, 1, 18, 0),
                end=datetime(2022, 6, 1, 19, 0),
            ),
            DurationHoursResult(
                hour=datetime(2022, 6, 1, 19, 0),
                duration=1,
                start=datetime(2022, 6, 1, 19, 0),
                end=datetime(2022, 6, 1, 20, 0),
            ),
            DurationHoursResult(
                hour=datetime(2022, 6, 1, 20, 0),
                duration=1,
                start=datetime(2022, 6, 1, 20, 0),
                end=datetime(2022, 6, 1, 21, 0),
            ),
            DurationHoursResult(
                hour=datetime(2022, 6, 1, 21, 0),
                duration=1,
                start=datetime(2022, 6, 1, 21, 0),
                end=datetime(2022, 6, 1, 22, 0),
            ),
            DurationHoursResult(
                hour=datetime(2022, 6, 1, 22, 0),
                duration=1,
                start=datetime(2022, 6, 1, 22, 0),
                end=datetime(2022, 6, 1, 23, 0),
            ),
            DurationHoursResult(
                hour=datetime(2022, 6, 1, 23, 0),
                duration=1,
                start=datetime(2022, 6, 1, 23, 0),
                end=datetime(2022, 6, 2, 0, 0),
            ),
        ]

    def test_full_hour(self):
        start_time = datetime(year=2022, month=6, day=1, hour=5, minute=0)
        assert list(split_duration_into_hours(start_date=start_time, duration=3 / 24)) == [  # 3 hours
            DurationHoursResult(
                hour=datetime(2022, 6, 1, 5, 0),
                duration=1,
                start=datetime(2022, 6, 1, 5, 0),
                end=datetime(2022, 6, 1, 6, 0),
            ),
            DurationHoursResult(
                hour=datetime(2022, 6, 1, 6, 0),
                duration=1,
                start=datetime(2022, 6, 1, 6, 0),
                end=datetime(2022, 6, 1, 7, 0),
            ),
            DurationHoursResult(
                hour=datetime(2022, 6, 1, 7, 0),
                duration=1,
                start=datetime(2022, 6, 1, 7, 0),
                end=datetime(2022, 6, 1, 8, 0),
            ),
        ]

    def test_part_hour(self):
        start_time = datetime(year=2022, month=6, day=1, hour=5, minute=15)
        assert list(split_duration_into_hours(start_date=start_time, duration=3.50 / 24)) == [  # 3 hours 30 minutes
            DurationHoursResult(
                hour=datetime(2022, 6, 1, 5, 0),
                duration=3 / 4,
                start=datetime(2022, 6, 1, 5, 15),
                end=datetime(2022, 6, 1, 6, 0),
            ),
            DurationHoursResult(
                hour=datetime(2022, 6, 1, 6, 0),
                duration=1,
                start=datetime(2022, 6, 1, 6, 0),
                end=datetime(2022, 6, 1, 7, 0),
            ),
            DurationHoursResult(
                hour=datetime(2022, 6, 1, 7, 0),
                duration=1,
                start=datetime(2022, 6, 1, 7, 0),
                end=datetime(2022, 6, 1, 8, 0),
            ),
            DurationHoursResult(
                hour=datetime(2022, 6, 1, 8, 0),
                duration=3 / 4,
                start=datetime(2022, 6, 1, 8, 0),
                end=datetime(2022, 6, 1, 8, 45),
            ),
        ]

    def test_single_hour(self):
        start_time = datetime(year=2022, month=6, day=1, hour=5, minute=30)
        assert list(split_duration_into_hours(start_date=start_time, duration=0.25 / 24)) == [  # 15 minutes
            DurationHoursResult(
                hour=datetime(2022, 6, 1, 5, 0),
                duration=1 / 4,
                start=datetime(2022, 6, 1, 5, 30),
                end=datetime(2022, 6, 1, 5, 45),
            )
        ]


@pytest.mark.django_db
class TestUpdateWellPlannerActualStartDate:
    @pytest.mark.parametrize(
        'current_step',
        (WellPlannerWizardStep.WELL_REVIEWING, WellPlannerWizardStep.WELL_REPORTING),
    )
    def test_update_well_planner_actual_start_date(self, current_step: WellPlannerWizardStep):
        user = UserFactory()
        well_planner = WellPlannerFactory(
            actual_start_date=date(2022, 5, 1),
            current_step=current_step,
        )
        complete_step = WellPlannerCompleteStepFactory(well_planner=well_planner)
        emission_reduction_initiative = EmissionReductionInitiativeFactory(
            emission_management_plan=well_planner.emission_management_plan, deployment_date=date(2020, 1, 1)
        )
        complete_step.emission_reduction_initiatives.add(emission_reduction_initiative)
        actual_start_date = date(2022, 6, 1)

        well_planner = update_well_planner_actual_start_date(
            well_planner=well_planner, user=user, actual_start_date=actual_start_date
        )

        assert well_planner.actual_start_date == actual_start_date

    @pytest.mark.parametrize(
        'current_step',
        (
            set(WellPlannerWizardStep.values)
            - {WellPlannerWizardStep.WELL_REVIEWING, WellPlannerWizardStep.WELL_REPORTING}
        ),
    )
    def test_should_raise_error_for_invalid_current_step(self, current_step: WellPlannerWizardStep):
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=current_step)

        with pytest.raises(ValidationError) as ex:
            update_well_planner_actual_start_date(
                well_planner=well_planner, user=user, actual_start_date=date(2022, 6, 1)
            )

        assert ex.value.message == "Actual start date cannot be updated right now."


@pytest.mark.django_db
class TestAvailableEmissionReductionInitiatives:
    def test_available_emission_reduction_initiatives(self):
        well_planner = WellPlannerFactory(planned_start_date=date(2022, 6, 1))
        emission_reduction_initiative = EmissionReductionInitiativeFactory(
            emission_management_plan=well_planner.emission_management_plan, deployment_date=date(2022, 5, 1)
        )
        EmissionReductionInitiativeFactory(
            emission_management_plan=well_planner.emission_management_plan, deployment_date=date(2023, 1, 1)
        )
        EmissionReductionInitiativeFactory(
            emission_management_plan__baseline=well_planner.baseline, deployment_date=date(2020, 6, 1)
        )
        EmissionReductionInitiativeFactory(deployment_date=date(2020, 1, 1))
        EmissionReductionInitiativeFactory(emission_management_plan=well_planner.emission_management_plan, deleted=True)

        emission_reduction_initiatives = available_emission_reduction_initiatives(well_planner=well_planner)

        assert list(emission_reduction_initiatives) == [emission_reduction_initiative]

    def test_no_emission_management_plan(self):
        well_planner = WellPlannerFactory(emission_management_plan=None, planned_start_date=date(2022, 6, 1))
        EmissionReductionInitiativeFactory(
            emission_management_plan__baseline=well_planner.baseline, deployment_date=date(2022, 5, 1)
        )

        emission_reduction_initiatives = available_emission_reduction_initiatives(well_planner=well_planner)

        assert list(emission_reduction_initiatives) == []
