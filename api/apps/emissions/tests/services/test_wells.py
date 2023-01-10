import datetime
from datetime import date
from unittest.mock import MagicMock

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from pytest_mock import MockerFixture

from apps.emissions.factories import (
    AssetFactory,
    BaselineFactory,
    BaselineInputFactory,
    CompleteHelicopterUseFactory,
    CompleteVesselUseFactory,
    EmissionManagementPlanFactory,
    EmissionReductionInitiativeFactory,
    ExternalEnergySupplyFactory,
    HelicopterTypeFactory,
    PlannedHelicopterUseFactory,
    PlannedVesselUseFactory,
    VesselTypeFactory,
    WellNameFactory,
)
from apps.emissions.factories.wells import (
    BaseCO2Factory,
    BaselineCO2Factory,
    TargetCO2ReductionFactory,
    BaselineNOXFactory,
    TargetCO2Factory,
    TargetNOXFactory,
)
from apps.emissions.models import (
    AssetSeason,
    BaselineCO2,
    CompleteHelicopterUse,
    CompleteVesselUse,
    EmissionReductionInitiativeType,
    PlannedHelicopterUse,
    PlannedVesselUse,
    TargetCO2,
    TargetCO2Reduction,
)
from apps.emissions.models.wells import BaseCO2, BaselineNOX, TargetNOX, TargetNOXReduction
from apps.emissions.services import (
    create_complete_helicopter_use,
    create_complete_vessel_use,
    create_planned_helicopter_use,
    create_planned_vessel_use,
    create_well,
    create_well_name,
    delete_complete_helicopter_use,
    delete_complete_vessel_use,
    delete_planned_helicopter_use,
    delete_planned_vessel_use,
    delete_well,
    duplicate_well,
    update_complete_helicopter_use,
    update_complete_vessel_use,
    update_planned_helicopter_use,
    update_planned_vessel_use,
    update_well,
    update_well_planned_start_date,
    validate_helicopter_use_data,
    validate_well_data,
)
from apps.emissions.services.calculator import (
    BaselineCO2Data,
    TargetCO2Data,
    multiply_baseline_co2,
    multiply_baseline_nox,
    multiply_target_co2,
    multiply_target_nox,
)
from apps.emissions.services.calculator.baseline import BaselineNOXData
from apps.emissions.services.calculator.target import TargetNOXData
from apps.emissions.services.wells import (
    EmissionReduction,
    calculate_baselines,
    calculate_planned_emissions,
    calculate_targets,
    get_co2_emissions,
    get_emission_reductions,
)
from apps.tenants.factories import TenantFactory, UserFactory
from apps.wells.factories import WellPlannerCompleteStepFactory, WellPlannerFactory, WellPlannerPlannedStepFactory
from apps.wells.models import WellPlannerWizardStep


@pytest.mark.django_db
class TestDeleteWell:
    def test_should_delete_well(self):
        user = UserFactory()
        well_planner = WellPlannerFactory()

        assert well_planner.deleted is False

        delete_well(user=user, well=well_planner)

        assert well_planner.deleted is True


@pytest.mark.django_db
class TestDuplicateWell:
    @pytest.mark.parametrize(
        'current_step',
        (
            WellPlannerWizardStep.WELL_PLANNING,
            WellPlannerWizardStep.WELL_REVIEWING,
            WellPlannerWizardStep.WELL_REPORTING,
        ),
    )
    def test_should_duplicate_well(
        self, current_step: WellPlannerWizardStep, mocked_calculate_planned_emissions: MagicMock
    ):
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=current_step)
        planned_steps = WellPlannerPlannedStepFactory.create_batch(2, well_planner=well_planner)
        planned_helicopter_uses = PlannedHelicopterUseFactory.create_batch(2, well_planner=well_planner)
        planned_vessel_uses = PlannedVesselUseFactory.create_batch(2, well_planner=well_planner)

        WellPlannerCompleteStepFactory.create_batch(2, well_planner=well_planner)
        CompleteHelicopterUseFactory.create_batch(2, well_planner=well_planner)
        CompleteVesselUseFactory.create_batch(2, well_planner=well_planner)

        duplicated_well_planner = duplicate_well(user=user, well=well_planner)

        assert duplicated_well_planner.sidetrack == f'{well_planner.sidetrack} - Copy'
        assert duplicated_well_planner.current_step == WellPlannerWizardStep.WELL_PLANNING
        assert duplicated_well_planner.actual_start_date is None
        assert duplicated_well_planner.deleted is False

        for attribute in {
            'name',
            'asset',
            'baseline',
            'emission_management_plan',
            'description',
            'type',
            'location',
            'field',
            'planned_start_date',
            'fuel_type',
            'fuel_density',
            'co2_per_fuel',
            'nox_per_fuel',
            'co2_tax',
            'nox_tax',
            'fuel_cost',
            'boilers_co2_per_fuel',
            'boilers_nox_per_fuel',
        }:
            assert getattr(duplicated_well_planner, attribute) == getattr(well_planner, attribute)

        assert duplicated_well_planner.planned_steps.count() == 2

        for planned_step, duplicated_planned_step in zip(
            planned_steps, duplicated_well_planner.planned_steps.order_by('pk')
        ):
            assert duplicated_planned_step.well_planner == duplicated_well_planner

            for attribute in {
                'phase',
                'mode',
                'season',
                'carbon_capture_storage_system_quantity',
                'well_section_length',
                'duration',
                'waiting_on_weather',
                'improved_duration',
                "comment",
                'external_energy_supply_enabled',
                "external_energy_supply_quota",
            }:
                assert getattr(planned_step, attribute) == getattr(duplicated_planned_step, attribute)

        assert duplicated_well_planner.plannedhelicopteruse_set.count() == 2

        for planned_helicopter_use, duplicated_planned_helicopter_use in zip(
            planned_helicopter_uses, duplicated_well_planner.plannedhelicopteruse_set.all()
        ):
            assert duplicated_planned_helicopter_use.well_planner == duplicated_well_planner

            helicopter_use_fields = [
                'helicopter_type',
                'trips',
                'trip_duration',
                'exposure_against_current_well',
                'quota_obligation',
            ]
            for attribute in helicopter_use_fields:
                assert getattr(planned_helicopter_use, attribute) == getattr(
                    duplicated_planned_helicopter_use, attribute
                )

        assert duplicated_well_planner.plannedvesseluse_set.count() == 2

        for planned_vessel_use, duplicated_planned_vessel_use in zip(
            planned_vessel_uses, duplicated_well_planner.plannedvesseluse_set.all()
        ):
            assert duplicated_planned_vessel_use.well_planner == duplicated_well_planner

            vessel_use_fields = [
                'vessel_type',
                'season',
                'duration',
                'exposure_against_current_well',
                'waiting_on_weather',
                'quota_obligation',
            ]
            for attribute in vessel_use_fields:
                assert getattr(planned_vessel_use, attribute) == getattr(duplicated_planned_vessel_use, attribute)

        assert duplicated_well_planner.complete_steps.count() == 0
        assert duplicated_well_planner.completehelicopteruse_set.count() == 0
        assert duplicated_well_planner.completevesseluse_set.count() == 0

        mocked_calculate_planned_emissions.assert_called_once_with(duplicated_well_planner)

    @pytest.mark.freeze_time('2022-05-11')
    def test_name_and_sidetrack_must_be_unique(self):
        user = UserFactory()
        well_planner = WellPlannerFactory(sidetrack='0001')

        first_copy = duplicate_well(user=user, well=well_planner)

        assert first_copy.name == well_planner.name
        assert first_copy.sidetrack == '0001 - Copy'

        second_copy = duplicate_well(user=user, well=well_planner)

        assert second_copy.name == well_planner.name
        assert second_copy.sidetrack == '0001 - Copy - 11.05.2022 00:00:00'

        with pytest.raises(ValidationError) as ex:
            duplicate_well(user=user, well=well_planner)

        assert ex.value.messages == ["Unable to duplicate the well."]


@pytest.mark.django_db
class TestValidateWellData:
    def test_should_raise_error_for_different_asset_tenant(self):
        asset = AssetFactory(draft=False)
        tenant = TenantFactory()
        well_name = WellNameFactory(tenant=asset.tenant)

        with pytest.raises(ValidationError) as ex:
            validate_well_data(tenant=tenant, asset=asset, name=well_name)

        assert ex.value.message_dict == {"asset": ["Chosen asset is not a valid choice."]}

    def test_should_raise_error_for_different_well_name_tenant(self):
        tenant = TenantFactory()
        asset = AssetFactory(draft=False, tenant=tenant)
        well_name = WellNameFactory()

        with pytest.raises(ValidationError) as ex:
            validate_well_data(tenant=tenant, asset=asset, name=well_name)

        assert ex.value.message_dict == {"name": ["Chosen name is not a valid choice."]}

    def test_should_raise_error_for_draft_asset(self):
        asset = AssetFactory(draft=True)
        well_name = WellNameFactory(tenant=asset.tenant)

        with pytest.raises(ValidationError) as ex:
            validate_well_data(tenant=asset.tenant, asset=asset, name=well_name)

        assert ex.value.message_dict == {"asset": ["Chosen asset is not a valid choice."]}

    def test_should_raise_error_for_deleted_asset(self):
        asset = AssetFactory(draft=False, deleted=True)
        well_name = WellNameFactory(tenant=asset.tenant)

        with pytest.raises(ValidationError) as ex:
            validate_well_data(tenant=asset.tenant, asset=asset, name=well_name)

        assert ex.value.message_dict == {"asset": ["Chosen asset is not a valid choice."]}


@pytest.mark.django_db
class TestCreateWell:
    def test_should_create_well(self, well_data: dict):
        user = UserFactory()
        asset = AssetFactory(draft=False)
        baseline = BaselineFactory(active=True, draft=False, asset=asset)
        name = WellNameFactory(tenant=asset.tenant)
        data = {
            "name": name,
            "asset": asset,
            **well_data,
        }

        well_planner = create_well(
            tenant=asset.tenant,
            user=user,
            **data,
        )

        assert well_planner.pk is not None
        assert well_planner.current_step == WellPlannerWizardStep.WELL_PLANNING
        assert well_planner.baseline == baseline
        assert well_planner.emission_management_plan is None
        assert well_planner.planned_start_date == timezone.now().date()
        assert well_planner.actual_start_date is None
        assert well_planner.deleted is False

        for field, value in data.items():
            assert getattr(well_planner, field) == value

    def test_should_create_well_with_baseline(self, well_data: dict):
        user = UserFactory()
        asset = AssetFactory(draft=False)
        name = WellNameFactory(tenant=asset.tenant)
        baseline = BaselineFactory(asset=asset, active=True)
        BaselineFactory(asset=asset, active=False)
        BaselineFactory(active=True)
        data = {
            "name": name,
            "asset": asset,
            **well_data,
        }

        well_planner = create_well(
            tenant=asset.tenant,
            user=user,
            **data,
        )

        assert well_planner.baseline == baseline
        assert well_planner.emission_management_plan is None

    def test_should_create_well_with_emission_management_plan(self, well_data: dict):
        user = UserFactory()
        asset = AssetFactory(draft=False)
        name = WellNameFactory(tenant=asset.tenant)
        baseline = BaselineFactory(asset=asset, active=True)
        emission_management_plan = EmissionManagementPlanFactory(baseline=baseline, active=True)
        EmissionManagementPlanFactory(baseline=baseline, active=False)
        EmissionManagementPlanFactory(baseline__asset=asset, baseline__active=False, baseline__draft=False, active=True)
        EmissionManagementPlanFactory(active=True)
        data = {
            "name": name,
            "asset": asset,
            **well_data,
        }

        well_planner = create_well(
            tenant=asset.tenant,
            user=user,
            **data,
        )

        assert well_planner.baseline == baseline
        assert well_planner.emission_management_plan == emission_management_plan

    def test_should_validate_well_data(self, well_data: dict, mocker):
        mocked_validate_well_data = mocker.patch("apps.emissions.services.wells.validate_well_data")
        user = UserFactory()
        asset = AssetFactory(draft=False)
        name = WellNameFactory(tenant=asset.tenant)
        BaselineFactory(active=True, draft=False, asset=asset)
        data = {
            "name": name,
            "asset": asset,
            **well_data,
        }

        create_well(
            tenant=asset.tenant,
            user=user,
            **data,
        )

        mocked_validate_well_data.assert_called_once_with(tenant=asset.tenant, asset=asset, name=name)

    def test_should_raise_error_for_duplicate_name_and_sidetrack(self, well_data: dict):
        user = UserFactory()
        asset = AssetFactory(draft=False)
        name = WellNameFactory(tenant=asset.tenant)
        BaselineFactory(asset=asset, active=True, draft=False)
        WellPlannerFactory(name=name, sidetrack=well_data["sidetrack"])
        data = {
            "name": name,
            "asset": asset,
            **well_data,
        }

        with pytest.raises(ValidationError) as ex:
            create_well(
                tenant=asset.tenant,
                user=user,
                **data,
            )

        assert ex.value.message_dict == {'name': ['Well name and sidetrack are already used.']}

    def test_name_and_sidetrack_for_deleted_well_are_no_longer_unique(self, well_data: dict):
        user = UserFactory()
        asset = AssetFactory(draft=False)
        name = WellNameFactory(tenant=asset.tenant)
        BaselineFactory(asset=asset, active=True, draft=False)
        WellPlannerFactory(name=name, sidetrack=well_data["sidetrack"], deleted=True)
        data = {
            "name": name,
            "asset": asset,
            **well_data,
        }

        create_well(
            tenant=asset.tenant,
            user=user,
            **data,
        )


@pytest.fixture
def mocked_calculate_planned_emissions(mocker: MockerFixture):
    return mocker.patch("apps.emissions.services.wells.calculate_planned_emissions")


@pytest.mark.django_db
class TestUpdateWell:
    def test_should_update_well(self, well_data: dict, mocked_calculate_planned_emissions: MagicMock):
        user = UserFactory()
        asset = AssetFactory(draft=False)
        baseline = BaselineFactory(asset=asset)
        emission_management_plan = EmissionManagementPlanFactory(baseline=baseline)
        well_planner = WellPlannerFactory(
            asset__draft=False,
            current_step=WellPlannerWizardStep.WELL_PLANNING,
            baseline=baseline,
            emission_management_plan=emission_management_plan,
        )
        data = {
            "name": well_planner.name,
            "asset": well_planner.asset,
            **well_data,
        }

        updated_well_planner = update_well(well_planner=well_planner, user=user, **data)

        assert updated_well_planner.pk == well_planner.pk
        assert updated_well_planner.baseline == baseline
        assert updated_well_planner.emission_management_plan == emission_management_plan

        for field, value in data.items():
            assert getattr(updated_well_planner, field) == value

        mocked_calculate_planned_emissions.assert_called_once_with(well_planner)

    def test_should_update_asset(self, well_data):
        user = UserFactory()
        tenant = TenantFactory()
        asset = AssetFactory(draft=False, tenant=tenant)
        name = WellNameFactory(tenant=tenant)
        baseline = BaselineFactory(asset=asset, active=True)
        emission_management_plan = EmissionManagementPlanFactory(baseline=baseline, active=True)
        well_planner = WellPlannerFactory(
            current_step=WellPlannerWizardStep.WELL_PLANNING, asset__tenant=tenant, asset__draft=False, name=name
        )
        data = {
            "name": name,
            "asset": asset,
            **well_data,
        }

        assert well_planner.baseline != baseline
        assert well_planner.emission_management_plan != emission_management_plan

        updated_well_planner = update_well(well_planner=well_planner, user=user, **data)

        assert updated_well_planner.pk == well_planner.pk
        assert updated_well_planner.baseline == baseline
        assert updated_well_planner.emission_management_plan == emission_management_plan

    def test_should_validate_well_data(self, well_data, mocker):
        mocked_validate_well_data = mocker.patch("apps.emissions.services.wells.validate_well_data")
        user = UserFactory()
        tenant = TenantFactory()
        name = WellNameFactory(tenant=tenant)
        asset = AssetFactory(draft=False, tenant=tenant)
        BaselineFactory(asset=asset, active=True)
        well_planner = WellPlannerFactory(current_step=WellPlannerWizardStep.WELL_PLANNING, asset=asset, name=name)
        data = {
            "name": name,
            "asset": asset,
            **well_data,
        }

        update_well(well_planner=well_planner, user=user, **data)

        mocked_validate_well_data.assert_called_once_with(tenant=tenant, asset=asset, name=name)

    @pytest.mark.parametrize(
        'current_step',
        (set(WellPlannerWizardStep.values) - {WellPlannerWizardStep.WELL_PLANNING}),
    )
    def test_should_raise_error_for_invalid_current_step(self, current_step: WellPlannerWizardStep, well_data: dict):
        user = UserFactory()
        well_planner = WellPlannerFactory(
            current_step=current_step,
            asset__draft=False,
        )
        data = {
            "name": well_planner.name,
            "asset": well_planner.asset,
            **well_data,
        }

        with pytest.raises(ValidationError) as ex:
            update_well(well_planner=well_planner, user=user, **data)

        assert ex.value.message == "Well cannot be updated right now."

    def test_should_raise_error_for_updated_asset_with_existing_phases(self, well_data: dict):
        user = UserFactory()
        tenant = TenantFactory()
        asset = AssetFactory(draft=False, tenant=tenant)
        BaselineFactory(asset=asset, active=True)
        well_planner = WellPlannerFactory(current_step=WellPlannerWizardStep.WELL_PLANNING, asset__tenant=tenant)
        WellPlannerPlannedStepFactory(well_planner=well_planner)
        data = {
            "asset": asset,
            "name": well_planner.name,
            **well_data,
        }

        with pytest.raises(ValidationError) as ex:
            update_well(well_planner=well_planner, user=user, **data)

        assert ex.value.message_dict == {'asset': ['Asset cannot be changed for a well with existing phases.']}

    def test_should_raise_error_for_duplicate_name_and_sidetrack(self, well_data: dict):
        user = UserFactory()
        tenant = TenantFactory()
        well_planner = WellPlannerFactory(
            asset__tenant=tenant,
            asset__draft=False,
            current_step=WellPlannerWizardStep.WELL_PLANNING,
            sidetrack="old sidetrack",
        )
        WellPlannerFactory(asset__tenant=tenant, name=well_planner.name, sidetrack=well_data["sidetrack"])
        data = {
            "asset": well_planner.asset,
            "name": well_planner.name,
            **well_data,
        }

        with pytest.raises(ValidationError) as ex:
            update_well(
                well_planner=well_planner,
                user=user,
                **data,
            )

        assert ex.value.message_dict == {'name': ['Well name and sidetrack are already used.']}

    def test_name_and_sidetrack_for_deleted_well_are_no_longer_unique(self, well_data: dict):
        user = UserFactory()
        well_planner = WellPlannerFactory(
            current_step=WellPlannerWizardStep.WELL_PLANNING,
            asset__draft=False,
        )
        WellPlannerFactory(name=well_planner.name, sidetrack=well_data["sidetrack"], deleted=True)
        data = {
            "asset": well_planner.asset,
            "name": well_planner.name,
            **well_data,
        }

        update_well(
            well_planner=well_planner,
            user=user,
            **data,
        )


@pytest.mark.django_db
class TestCreateWellName:
    def test_should_create_well_name(self):
        user = UserFactory()
        tenant = TenantFactory()
        data = {
            "name": "Well name",
        }
        WellNameFactory(name=data["name"])

        well_name = create_well_name(
            tenant=tenant,
            user=user,
            **data,
        )

        well_name.refresh_from_db()
        assert well_name.tenant == tenant

        for field, value in data.items():
            assert getattr(well_name, field) == value

    def test_should_raise_error_for_duplicate_name(self, well_data: dict):
        user = UserFactory()
        tenant = TenantFactory()
        data = {
            "name": "Well name",
        }
        WellNameFactory(name=data["name"], tenant=tenant)

        with pytest.raises(ValidationError) as ex:
            create_well_name(
                tenant=tenant,
                user=user,
                **data,
            )

        assert ex.value.message_dict == {'name': ['Well name is already used.']}


@pytest.mark.django_db
class TestCreatePlannedVesselUse:
    def test_should_create_planned_vessel_use(
        self, vessel_use_data: dict, mocked_calculate_planned_emissions: MagicMock
    ):
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=WellPlannerWizardStep.WELL_PLANNING)
        vessel_type = VesselTypeFactory(tenant=well_planner.asset.tenant)
        PlannedVesselUseFactory(well_planner=well_planner, vessel_type=vessel_type, season=AssetSeason.WINTER)

        data = {"well_planner": well_planner, "vessel_type": vessel_type, **vessel_use_data}

        planned_vessel_use = create_planned_vessel_use(user=user, **data)

        for field, value in data.items():
            assert getattr(planned_vessel_use, field) == value

        mocked_calculate_planned_emissions.assert_called_once_with(well_planner)

    @pytest.mark.parametrize(
        'current_step', (set(WellPlannerWizardStep.values) - {WellPlannerWizardStep.WELL_PLANNING})
    )
    def test_should_raise_error_for_invalid_current_step(
        self, current_step: WellPlannerWizardStep, vessel_use_data: dict
    ):
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=current_step)
        vessel_type = VesselTypeFactory(tenant=well_planner.asset.tenant)

        data = {"well_planner": well_planner, "vessel_type": vessel_type, **vessel_use_data}

        with pytest.raises(ValidationError) as ex:
            create_planned_vessel_use(user=user, **data)

        assert ex.value.message == "Vessel cannot be created right now."

    def test_should_raise_for_unknown_vessel_type(self, vessel_use_data: dict):
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=WellPlannerWizardStep.WELL_PLANNING)
        vessel_type = VesselTypeFactory()

        with pytest.raises(ValidationError) as ex:
            create_planned_vessel_use(user=user, well_planner=well_planner, vessel_type=vessel_type, **vessel_use_data)

        assert ex.value.message_dict == {"vessel_type": ["Chosen vessel is not a valid choice."]}

    def test_should_raise_for_deleted_vessel_type(self, vessel_use_data: dict):
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=WellPlannerWizardStep.WELL_PLANNING)
        vessel_type = VesselTypeFactory(tenant=well_planner.asset.tenant, deleted=True)

        with pytest.raises(ValidationError) as ex:
            create_planned_vessel_use(user=user, well_planner=well_planner, vessel_type=vessel_type, **vessel_use_data)

        assert ex.value.message_dict == {"vessel_type": ["Chosen vessel is not a valid choice."]}


@pytest.mark.django_db
class TestUpdatePlannedVesselUse:
    def test_should_update_planned_vessel_use(
        self, vessel_use_data: dict, mocked_calculate_planned_emissions: MagicMock
    ):
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=WellPlannerWizardStep.WELL_PLANNING)
        vessel_type = VesselTypeFactory(tenant=well_planner.asset.tenant)
        planned_vessel_use = PlannedVesselUseFactory(
            well_planner=well_planner, season=AssetSeason.SUMMER, duration=3.5, waiting_on_weather=5
        )
        PlannedVesselUseFactory(
            well_planner=well_planner, vessel_type=vessel_type, season=AssetSeason.WINTER, duration=3.5
        )

        data = {"vessel_type": vessel_type, **vessel_use_data}

        updated_planned_vessel_use = update_planned_vessel_use(user=user, planned_vessel_use=planned_vessel_use, **data)

        assert updated_planned_vessel_use.pk == planned_vessel_use.pk

        for field, value in data.items():
            assert getattr(updated_planned_vessel_use, field) == value

        mocked_calculate_planned_emissions.assert_called_once_with(well_planner)

    @pytest.mark.parametrize(
        'current_step', (set(WellPlannerWizardStep.values) - {WellPlannerWizardStep.WELL_PLANNING})
    )
    def test_should_raise_error_for_invalid_current_step(
        self, current_step: WellPlannerWizardStep, vessel_use_data: dict
    ):
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=current_step)
        planned_vessel_use = PlannedVesselUseFactory(well_planner=well_planner)
        vessel_type = VesselTypeFactory(tenant=well_planner.asset.tenant)

        data = {"vessel_type": vessel_type, **vessel_use_data}

        with pytest.raises(ValidationError) as ex:
            update_planned_vessel_use(user=user, planned_vessel_use=planned_vessel_use, **data)

        assert ex.value.message == "Vessel cannot be updated right now."

    def test_should_raise_for_unknown_vessel_type(self, vessel_use_data: dict):
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=WellPlannerWizardStep.WELL_PLANNING)
        planned_vessel_use = PlannedVesselUseFactory(well_planner=well_planner)
        vessel_type = VesselTypeFactory()

        with pytest.raises(ValidationError) as ex:
            update_planned_vessel_use(
                user=user, planned_vessel_use=planned_vessel_use, vessel_type=vessel_type, **vessel_use_data
            )

        assert ex.value.message_dict == {"vessel_type": ["Chosen vessel is not a valid choice."]}

    def test_should_raise_for_deleted_vessel_type(self, vessel_use_data: dict):
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=WellPlannerWizardStep.WELL_PLANNING)
        planned_vessel_use = PlannedVesselUseFactory(well_planner=well_planner)
        vessel_type = VesselTypeFactory(tenant=well_planner.asset.tenant, deleted=True)

        with pytest.raises(ValidationError) as ex:
            update_planned_vessel_use(
                user=user, planned_vessel_use=planned_vessel_use, vessel_type=vessel_type, **vessel_use_data
            )

        assert ex.value.message_dict == {"vessel_type": ["Chosen vessel is not a valid choice."]}


@pytest.mark.django_db
class TestDeletePlannedVesselUse:
    def test_should_delete_planned_vessel_use(self, mocked_calculate_planned_emissions: MagicMock):
        user = UserFactory()
        planned_vessel_use = PlannedVesselUseFactory(well_planner__current_step=WellPlannerWizardStep.WELL_PLANNING)

        delete_planned_vessel_use(user=user, planned_vessel_use=planned_vessel_use)

        assert not PlannedVesselUse.objects.filter(pk=planned_vessel_use.pk).exists()

        mocked_calculate_planned_emissions.assert_called_once_with(planned_vessel_use.well_planner)

    @pytest.mark.parametrize(
        'current_step', (set(WellPlannerWizardStep.values) - {WellPlannerWizardStep.WELL_PLANNING})
    )
    def test_should_raise_error_for_invalid_current_step(self, current_step: WellPlannerWizardStep):
        user = UserFactory()
        planned_vessel_use = PlannedVesselUseFactory(well_planner__current_step=current_step)

        with pytest.raises(ValidationError) as ex:
            delete_planned_vessel_use(user=user, planned_vessel_use=planned_vessel_use)

        assert ex.value.message == "Vessel cannot be deleted right now."


@pytest.mark.django_db
class TestCreateCompleteVesselUse:
    def test_should_create_complete_vessel_use(self, vessel_use_data: dict):
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=WellPlannerWizardStep.WELL_REVIEWING)
        vessel_type = VesselTypeFactory(tenant=well_planner.asset.tenant)
        CompleteVesselUseFactory(well_planner=well_planner, vessel_type=vessel_type, season=AssetSeason.SUMMER)

        data = {"vessel_type": vessel_type, **vessel_use_data}

        complete_vessel_use = create_complete_vessel_use(user=user, well_planner=well_planner, **data)

        assert complete_vessel_use.approved is False

        for field, value in data.items():
            assert getattr(complete_vessel_use, field) == value

    @pytest.mark.parametrize(
        'current_step',
        (set(WellPlannerWizardStep.values) - {WellPlannerWizardStep.WELL_REVIEWING}),
    )
    def test_should_raise_error_for_invalid_current_step(
        self, current_step: WellPlannerWizardStep, vessel_use_data: dict
    ):
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=current_step)
        vessel_type = VesselTypeFactory(tenant=well_planner.asset.tenant)

        data = {"vessel_type": vessel_type, **vessel_use_data}

        with pytest.raises(ValidationError) as ex:
            create_complete_vessel_use(user=user, well_planner=well_planner, **data)

        assert ex.value.message == "Vessel cannot be created right now."

    def test_should_raise_for_unknown_vessel_type(self, vessel_use_data: dict):
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=WellPlannerWizardStep.WELL_REVIEWING)
        vessel_type = VesselTypeFactory()

        with pytest.raises(ValidationError) as ex:
            create_complete_vessel_use(user=user, well_planner=well_planner, vessel_type=vessel_type, **vessel_use_data)

        assert ex.value.message_dict == {"vessel_type": ["Chosen vessel is not a valid choice."]}

    def test_should_raise_for_deleted_vessel_type(self, vessel_use_data: dict):
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=WellPlannerWizardStep.WELL_REVIEWING)
        vessel_type = VesselTypeFactory(tenant=well_planner.asset.tenant, deleted=True)

        with pytest.raises(ValidationError) as ex:
            create_complete_vessel_use(
                user=user,
                well_planner=well_planner,
                vessel_type=vessel_type,
                **vessel_use_data,
            )

        assert ex.value.message_dict == {"vessel_type": ["Chosen vessel is not a valid choice."]}


@pytest.mark.django_db
class TestUpdateCompleteVesselUse:
    def test_should_update_complete_vessel_use(self, vessel_use_data: dict):
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=WellPlannerWizardStep.WELL_REVIEWING)
        vessel_type = VesselTypeFactory(tenant=well_planner.asset.tenant)
        complete_vessel_use = CompleteVesselUseFactory(
            well_planner=well_planner, approved=True, season=AssetSeason.SUMMER, duration=3.5
        )
        CompleteVesselUseFactory(
            well_planner=well_planner, approved=True, vessel_type=vessel_type, season=AssetSeason.WINTER, duration=3.5
        )

        data = {"vessel_type": vessel_type, **vessel_use_data}

        updated_complete_vessel_use = update_complete_vessel_use(
            user=user, complete_vessel_use=complete_vessel_use, **data
        )

        assert updated_complete_vessel_use.pk == complete_vessel_use.pk
        assert updated_complete_vessel_use.approved is False

        for field, value in data.items():
            assert getattr(updated_complete_vessel_use, field) == value

    @pytest.mark.parametrize(
        'current_step',
        (set(WellPlannerWizardStep.values) - {WellPlannerWizardStep.WELL_REVIEWING}),
    )
    def test_should_raise_error_for_invalid_current_step(
        self, current_step: WellPlannerWizardStep, vessel_use_data: dict
    ):
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=current_step)
        complete_vessel_use = CompleteVesselUseFactory(well_planner=well_planner, approved=True)
        vessel_type = VesselTypeFactory(tenant=well_planner.asset.tenant)

        data = {"vessel_type": vessel_type, **vessel_use_data}

        with pytest.raises(ValidationError) as ex:
            update_complete_vessel_use(user=user, complete_vessel_use=complete_vessel_use, **data)

        assert ex.value.message == "Vessel cannot be updated right now."

    def test_should_raise_for_unknown_vessel_type(self, vessel_use_data: dict):
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=WellPlannerWizardStep.WELL_REVIEWING)
        complete_vessel_use = CompleteVesselUseFactory(well_planner=well_planner)
        vessel_type = VesselTypeFactory()

        with pytest.raises(ValidationError) as ex:
            update_complete_vessel_use(
                user=user, complete_vessel_use=complete_vessel_use, vessel_type=vessel_type, **vessel_use_data
            )

        assert ex.value.message_dict == {"vessel_type": ["Chosen vessel is not a valid choice."]}

    def test_should_raise_for_deleted_vessel_type(self, vessel_use_data: dict):
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=WellPlannerWizardStep.WELL_REVIEWING)
        complete_vessel_use = CompleteVesselUseFactory(well_planner=well_planner)
        vessel_type = VesselTypeFactory(tenant=well_planner.asset.tenant, deleted=True)

        with pytest.raises(ValidationError) as ex:
            update_complete_vessel_use(
                user=user, complete_vessel_use=complete_vessel_use, vessel_type=vessel_type, **vessel_use_data
            )

        assert ex.value.message_dict == {"vessel_type": ["Chosen vessel is not a valid choice."]}


@pytest.mark.django_db
class TestDeleteCompleteVesselUse:
    def test_should_delete_complete_vessel_use(self):
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=WellPlannerWizardStep.WELL_REVIEWING)
        complete_vessel_use = CompleteVesselUseFactory(well_planner=well_planner)

        delete_complete_vessel_use(user=user, complete_vessel_use=complete_vessel_use)

        assert not CompleteVesselUse.objects.filter(pk=complete_vessel_use.pk).exists()

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
        complete_vessel_use = CompleteVesselUseFactory(well_planner=well_planner)

        with pytest.raises(ValidationError) as ex:
            delete_complete_vessel_use(user=user, complete_vessel_use=complete_vessel_use)

        assert ex.value.message == "Vessel cannot be deleted right now."


@pytest.mark.django_db
class TestUpdateWellPlannedStartDate:
    def test_update_well_planned_start_date(self, mocked_calculate_planned_emissions: MagicMock):
        user = UserFactory()
        well_planner = WellPlannerFactory(
            planned_start_date=date(2022, 5, 1),
            current_step=WellPlannerWizardStep.WELL_PLANNING,
        )
        planned_step = WellPlannerPlannedStepFactory(well_planner=well_planner)
        emission_reduction_initiative = EmissionReductionInitiativeFactory(
            emission_management_plan=well_planner.emission_management_plan, deployment_date=date(2020, 1, 1)
        )
        planned_step.emission_reduction_initiatives.add(emission_reduction_initiative)
        BaselineInputFactory(
            baseline=well_planner.baseline, phase=planned_step.phase, mode=planned_step.mode, season=planned_step.season
        )
        ExternalEnergySupplyFactory(asset=well_planner.asset)
        planned_start_date = date(2022, 6, 1)

        well_planner = update_well_planned_start_date(
            well_planner=well_planner, user=user, planned_start_date=planned_start_date
        )

        assert well_planner.planned_start_date == planned_start_date

        mocked_calculate_planned_emissions.assert_called_once_with(well_planner)

    @pytest.mark.parametrize(
        'current_step',
        (set(WellPlannerWizardStep.values) - {WellPlannerWizardStep.WELL_PLANNING}),
    )
    def test_should_raise_error_for_invalid_current_step(self, current_step: WellPlannerWizardStep):
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=current_step)

        with pytest.raises(ValidationError) as ex:
            update_well_planned_start_date(well_planner=well_planner, user=user, planned_start_date=date(2022, 6, 1))

        assert ex.value.message == "Planned start date cannot be updated right now."

    def test_should_raise_error_for_not_deployed_emission_reduction_initiatives(self):
        user = UserFactory()
        well_planner = WellPlannerFactory(
            planned_start_date=date(2023, 1, 1),
            current_step=WellPlannerWizardStep.WELL_PLANNING,
        )
        planned_step = WellPlannerPlannedStepFactory(well_planner=well_planner)
        emission_reduction_initiative = EmissionReductionInitiativeFactory(
            name="Not deployed",
            emission_management_plan=well_planner.emission_management_plan,
            deployment_date=date(2023, 1, 1),
        )
        planned_step.emission_reduction_initiatives.add(emission_reduction_initiative)

        with pytest.raises(ValidationError) as ex:
            update_well_planned_start_date(well_planner=well_planner, user=user, planned_start_date=date(2022, 6, 1))

        assert (
            ex.value.message == "Unable to change planned start date. "
            f"Energy reduction initiative \"{emission_reduction_initiative.name}\" won't be deployed until that date."
        )


@pytest.mark.django_db
class TestValidateHelicopterUseData:
    def test_should_raise_for_different_tenant(self, helicopter_use_data: dict):
        well_planner = WellPlannerFactory(current_step=WellPlannerWizardStep.WELL_PLANNING)
        helicopter_type = HelicopterTypeFactory()

        with pytest.raises(ValidationError) as ex:
            validate_helicopter_use_data(
                tenant=well_planner.asset.tenant,
                helicopter_type=helicopter_type,
            )

        assert ex.value.message_dict == {"helicopter_type": ["Chosen helicopter is not a valid choice."]}

    def test_should_raise_for_deleted_helicopter_type(self, helicopter_use_data: dict):
        well_planner = WellPlannerFactory(current_step=WellPlannerWizardStep.WELL_PLANNING)
        helicopter_type = HelicopterTypeFactory(tenant=well_planner.asset.tenant, deleted=True)

        with pytest.raises(ValidationError) as ex:
            validate_helicopter_use_data(
                tenant=well_planner.asset.tenant,
                helicopter_type=helicopter_type,
            )

        assert ex.value.message_dict == {"helicopter_type": ["Chosen helicopter is not a valid choice."]}


@pytest.mark.django_db
class TestCreatePlannedHelicopterUse:
    def test_should_create_planned_helicopter_use(
        self, helicopter_use_data: dict, mocked_calculate_planned_emissions: MagicMock
    ):
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=WellPlannerWizardStep.WELL_PLANNING)
        helicopter_type = HelicopterTypeFactory(tenant=well_planner.asset.tenant)

        data = {"well_planner": well_planner, "helicopter_type": helicopter_type, **helicopter_use_data}

        planned_helicopter_use = create_planned_helicopter_use(user=user, **data)

        for field, value in data.items():
            assert getattr(planned_helicopter_use, field) == value

        mocked_calculate_planned_emissions.assert_called_once_with(well_planner)

    @pytest.mark.parametrize(
        'current_step', (set(WellPlannerWizardStep.values) - {WellPlannerWizardStep.WELL_PLANNING})
    )
    def test_should_raise_error_for_invalid_current_step(
        self, current_step: WellPlannerWizardStep, helicopter_use_data: dict
    ):
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=current_step)
        helicopter_type = HelicopterTypeFactory(tenant=well_planner.asset.tenant)

        data = {"well_planner": well_planner, "helicopter_type": helicopter_type, **helicopter_use_data}

        with pytest.raises(ValidationError) as ex:
            create_planned_helicopter_use(user=user, **data)

        assert ex.value.message == "Helicopter cannot be created right now."

    def test_should_validate_planned_helicopter_use_data(self, helicopter_use_data: dict, mocker):
        mocked_validate_helicopter_use_data = mocker.patch("apps.emissions.services.wells.validate_helicopter_use_data")
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=WellPlannerWizardStep.WELL_PLANNING)
        helicopter_type = HelicopterTypeFactory(tenant=well_planner.asset.tenant)
        data = {"well_planner": well_planner, "helicopter_type": helicopter_type, **helicopter_use_data}

        create_planned_helicopter_use(user=user, **data)

        mocked_validate_helicopter_use_data.assert_called_once_with(
            tenant=well_planner.asset.tenant, helicopter_type=helicopter_type
        )


@pytest.mark.django_db
class TestUpdatePlannedHelicopterUse:
    def test_should_update_planned_helicopter_use(
        self, helicopter_use_data: dict, mocked_calculate_planned_emissions: MagicMock
    ):
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=WellPlannerWizardStep.WELL_PLANNING)
        planned_helicopter_use = PlannedHelicopterUseFactory(well_planner=well_planner)
        helicopter_type = HelicopterTypeFactory(tenant=well_planner.asset.tenant)

        data = {"helicopter_type": helicopter_type, **helicopter_use_data}

        updated_planned_helicopter_use = update_planned_helicopter_use(
            user=user, planned_helicopter_use=planned_helicopter_use, **data
        )

        assert updated_planned_helicopter_use.pk == planned_helicopter_use.pk

        for field, value in data.items():
            assert getattr(updated_planned_helicopter_use, field) == value

        mocked_calculate_planned_emissions.assert_called_once_with(well_planner)

    @pytest.mark.parametrize(
        'current_step', (set(WellPlannerWizardStep.values) - {WellPlannerWizardStep.WELL_PLANNING})
    )
    def test_should_raise_error_for_invalid_current_step(
        self, current_step: WellPlannerWizardStep, helicopter_use_data: dict
    ):
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=current_step)
        planned_helicopter_use = PlannedHelicopterUseFactory(well_planner=well_planner)
        helicopter_type = HelicopterTypeFactory(tenant=well_planner.asset.tenant)

        data = {"helicopter_type": helicopter_type, **helicopter_use_data}

        with pytest.raises(ValidationError) as ex:
            update_planned_helicopter_use(user=user, planned_helicopter_use=planned_helicopter_use, **data)

        assert ex.value.message == "Helicopter cannot be updated right now."

    def test_should_validate_planned_helicopter_use_data(self, helicopter_use_data: dict, mocker):
        mocked_validate_helicopter_use_data = mocker.patch("apps.emissions.services.wells.validate_helicopter_use_data")
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=WellPlannerWizardStep.WELL_PLANNING)
        planned_helicopter_use = PlannedHelicopterUseFactory(well_planner=well_planner)
        helicopter_type = HelicopterTypeFactory(tenant=well_planner.asset.tenant)

        data = {"helicopter_type": helicopter_type, **helicopter_use_data}

        update_planned_helicopter_use(user=user, planned_helicopter_use=planned_helicopter_use, **data)

        mocked_validate_helicopter_use_data.assert_called_once_with(
            tenant=planned_helicopter_use.well_planner.asset.tenant, helicopter_type=helicopter_type
        )


@pytest.mark.django_db
class TestDeletePlannedHelicopterUse:
    def test_should_delete_planned_helicopter_use(self, mocked_calculate_planned_emissions: MagicMock):
        user = UserFactory()
        planned_helicopter_use = PlannedHelicopterUseFactory(
            well_planner__current_step=WellPlannerWizardStep.WELL_PLANNING
        )

        delete_planned_helicopter_use(user=user, planned_helicopter_use=planned_helicopter_use)

        assert not PlannedHelicopterUse.objects.filter(pk=planned_helicopter_use.pk).exists()

        mocked_calculate_planned_emissions.assert_called_once_with(planned_helicopter_use.well_planner)

    @pytest.mark.parametrize(
        'current_step', (set(WellPlannerWizardStep.values) - {WellPlannerWizardStep.WELL_PLANNING})
    )
    def test_should_raise_error_for_invalid_current_step(self, current_step: WellPlannerWizardStep):
        user = UserFactory()
        planned_helicopter_use = PlannedHelicopterUseFactory(well_planner__current_step=current_step)

        with pytest.raises(ValidationError) as ex:
            delete_planned_helicopter_use(user=user, planned_helicopter_use=planned_helicopter_use)

        assert ex.value.message == "Helicopter cannot be deleted right now."


@pytest.mark.django_db
class TestCreateCompleteHelicopterUse:
    def test_should_create_complete_helicopter_use(self, helicopter_use_data: dict):
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=WellPlannerWizardStep.WELL_REVIEWING)
        helicopter_type = HelicopterTypeFactory(tenant=well_planner.asset.tenant)

        data = {"well_planner": well_planner, "helicopter_type": helicopter_type, **helicopter_use_data}

        complete_helicopter_use = create_complete_helicopter_use(user=user, **data)

        assert complete_helicopter_use.approved is False

        for field, value in data.items():
            assert getattr(complete_helicopter_use, field) == value

    @pytest.mark.parametrize(
        'current_step',
        (set(WellPlannerWizardStep.values) - {WellPlannerWizardStep.WELL_REVIEWING}),
    )
    def test_should_raise_error_for_invalid_current_step(
        self, current_step: WellPlannerWizardStep, helicopter_use_data: dict
    ):
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=current_step)
        helicopter_type = HelicopterTypeFactory(tenant=well_planner.asset.tenant)

        data = {"well_planner": well_planner, "helicopter_type": helicopter_type, **helicopter_use_data}

        with pytest.raises(ValidationError) as ex:
            create_complete_helicopter_use(user=user, **data)

        assert ex.value.message == "Helicopter cannot be created right now."

    def test_should_validate_complete_helicopter_use_data(self, helicopter_use_data: dict, mocker):
        mocked_validate_helicopter_use_data = mocker.patch("apps.emissions.services.wells.validate_helicopter_use_data")
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=WellPlannerWizardStep.WELL_REVIEWING)
        helicopter_type = HelicopterTypeFactory(tenant=well_planner.asset.tenant)

        data = {"well_planner": well_planner, "helicopter_type": helicopter_type, **helicopter_use_data}

        create_complete_helicopter_use(user=user, **data)

        mocked_validate_helicopter_use_data.assert_called_once_with(
            tenant=well_planner.asset.tenant, helicopter_type=helicopter_type
        )


@pytest.mark.django_db
class TestUpdateCompleteHelicopterUse:
    def test_should_update_complete_helicopter_use(self, helicopter_use_data: dict):
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=WellPlannerWizardStep.WELL_REVIEWING)
        complete_helicopter_use = CompleteHelicopterUseFactory(well_planner=well_planner, approved=True)
        helicopter_type = HelicopterTypeFactory(tenant=well_planner.asset.tenant)

        data = {"helicopter_type": helicopter_type, **helicopter_use_data}

        updated_complete_helicopter_use = update_complete_helicopter_use(
            user=user, complete_helicopter_use=complete_helicopter_use, **data
        )

        assert updated_complete_helicopter_use.pk == complete_helicopter_use.pk
        assert updated_complete_helicopter_use.approved is False

        for field, value in data.items():
            assert getattr(updated_complete_helicopter_use, field) == value

    @pytest.mark.parametrize(
        'current_step',
        (set(WellPlannerWizardStep.values) - {WellPlannerWizardStep.WELL_REVIEWING}),
    )
    def test_should_raise_error_for_invalid_current_step(
        self, current_step: WellPlannerWizardStep, helicopter_use_data: dict
    ):
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=current_step)
        complete_helicopter_use = CompleteHelicopterUseFactory(well_planner=well_planner, approved=True)
        helicopter_type = HelicopterTypeFactory(tenant=well_planner.asset.tenant)

        data = {"helicopter_type": helicopter_type, **helicopter_use_data}

        with pytest.raises(ValidationError) as ex:
            update_complete_helicopter_use(user=user, complete_helicopter_use=complete_helicopter_use, **data)

        assert ex.value.message == "Helicopter cannot be updated right now."

    def test_should_validate_complete_helicopter_use_data(self, helicopter_use_data: dict, mocker):
        mocked_validate_helicopter_use_data = mocker.patch("apps.emissions.services.wells.validate_helicopter_use_data")
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=WellPlannerWizardStep.WELL_REVIEWING)
        complete_helicopter_use = CompleteHelicopterUseFactory(well_planner=well_planner, approved=True)
        helicopter_type = HelicopterTypeFactory(tenant=well_planner.asset.tenant)

        data = {"helicopter_type": helicopter_type, **helicopter_use_data}

        update_complete_helicopter_use(user=user, complete_helicopter_use=complete_helicopter_use, **data)

        mocked_validate_helicopter_use_data.assert_called_once_with(
            tenant=complete_helicopter_use.well_planner.asset.tenant, helicopter_type=helicopter_type
        )


@pytest.mark.django_db
class TestDeleteCompleteHelicopterUse:
    def test_should_delete_complete_helicopter_use(self):
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=WellPlannerWizardStep.WELL_REVIEWING)
        complete_helicopter_use = CompleteHelicopterUseFactory(well_planner=well_planner)

        delete_complete_helicopter_use(user=user, complete_helicopter_use=complete_helicopter_use)

        assert not CompleteHelicopterUse.objects.filter(pk=complete_helicopter_use.pk).exists()

    @pytest.mark.parametrize(
        'current_step',
        (set(WellPlannerWizardStep.values) - {WellPlannerWizardStep.WELL_REVIEWING}),
    )
    def test_should_raise_error_for_invalid_current_step(self, current_step: WellPlannerWizardStep):
        user = UserFactory()
        well_planner = WellPlannerFactory(current_step=current_step)
        complete_helicopter_use = CompleteHelicopterUseFactory(well_planner=well_planner)

        with pytest.raises(ValidationError) as ex:
            delete_complete_helicopter_use(user=user, complete_helicopter_use=complete_helicopter_use)

        assert ex.value.message == "Helicopter cannot be deleted right now."


@pytest.mark.django_db
class TestCalculateBaselines:
    @pytest.fixture
    def mock_baseline_co2_data(self) -> BaselineCO2Data:
        mock_baseline_co2 = BaselineCO2Data(
            asset=1000, boilers=2000, vessels=3000, helicopters=4000, materials=5000, external_energy_supply=6000
        )
        return mock_baseline_co2

    @pytest.fixture
    def mock_calculate_planned_step_baseline_co2(
        self, mocker: MockerFixture, mock_baseline_co2_data: BaselineCO2Data
    ) -> MagicMock:
        mock_calculate_planned_step_baseline_co2 = mocker.patch(
            "apps.emissions.services.wells.calculate_planned_step_baseline_co2"
        )
        mock_calculate_planned_step_baseline_co2.return_value = mock_baseline_co2_data
        return mock_calculate_planned_step_baseline_co2

    @pytest.fixture
    def mock_baseline_nox_data(self) -> BaselineNOXData:
        mock_baseline_nox = BaselineNOXData(
            asset=10000, boilers=20000, vessels=30000, helicopters=40000, external_energy_supply=60000
        )
        return mock_baseline_nox

    @pytest.fixture
    def mock_calculate_planned_step_baseline_nox(
        self, mocker: MockerFixture, mock_baseline_nox_data: BaselineNOXData
    ) -> MagicMock:
        mock_calculate_planned_step_baseline_nox = mocker.patch(
            "apps.emissions.services.wells.calculate_planned_step_baseline_nox"
        )
        mock_calculate_planned_step_baseline_nox.return_value = mock_baseline_nox_data
        return mock_calculate_planned_step_baseline_nox

    def test_should_calculate_baselines(
        self,
        mock_baseline_co2_data: BaselineCO2Data,
        mock_baseline_nox_data: BaselineNOXData,
        mock_calculate_planned_step_baseline_co2: MagicMock,
        mock_calculate_planned_step_baseline_nox: MagicMock,
    ):
        planned_start_datetime = datetime.datetime(2021, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
        well_plan = WellPlannerFactory(planned_start_date=planned_start_datetime)

        step_1 = WellPlannerPlannedStepFactory(well_planner=well_plan, duration=0.5)
        step_2 = WellPlannerPlannedStepFactory(well_planner=well_plan, duration=0.25)
        step_3 = WellPlannerPlannedStepFactory(well_planner=well_plan, duration=0.25)
        step_4 = WellPlannerPlannedStepFactory(well_planner=well_plan, duration=1.25)
        step_5 = WellPlannerPlannedStepFactory(well_planner=well_plan, duration=1.0)

        BaselineCO2Factory(planned_step=step_1)
        TargetCO2Factory(planned_step=step_1)
        BaselineNOXFactory(planned_step=step_1)
        TargetNOXFactory(planned_step=step_1)

        WellPlannerCompleteStepFactory(well_planner=well_plan)

        calculate_baselines(well_plan=well_plan)

        expected_baseline_co2_entries = [
            {
                "datetime": planned_start_datetime,
                "planned_step": step_1,
                **mock_baseline_co2_data,
            },
            {
                "datetime": planned_start_datetime + datetime.timedelta(days=0.5),
                "planned_step": step_2,
                **mock_baseline_co2_data,
            },
            {
                "datetime": planned_start_datetime + datetime.timedelta(days=0.75),
                "planned_step": step_3,
                **mock_baseline_co2_data,
            },
            {
                "datetime": planned_start_datetime + datetime.timedelta(days=1.0),
                "planned_step": step_4,
                **multiply_baseline_co2(baseline=mock_baseline_co2_data, multiplier=0.8),
            },
            {
                "datetime": planned_start_datetime + datetime.timedelta(days=2.0),
                "planned_step": step_4,
                **multiply_baseline_co2(baseline=mock_baseline_co2_data, multiplier=0.2),
            },
            {
                "datetime": planned_start_datetime + datetime.timedelta(days=2.25),
                "planned_step": step_5,
                **multiply_baseline_co2(baseline=mock_baseline_co2_data, multiplier=0.75),
            },
            {
                "datetime": planned_start_datetime + datetime.timedelta(days=3.0),
                "planned_step": step_5,
                **multiply_baseline_co2(baseline=mock_baseline_co2_data, multiplier=0.25),
            },
        ]

        for baseline_co2_data, baseline_co2 in zip(
            expected_baseline_co2_entries,
            BaselineCO2.objects.filter(planned_step__well_planner=well_plan).order_by('datetime'),
        ):
            assert baseline_co2_data['planned_step'] == baseline_co2.planned_step
            assert baseline_co2_data['datetime'] == baseline_co2.datetime
            assert baseline_co2_data['asset'] == baseline_co2.asset
            assert baseline_co2_data['vessels'] == baseline_co2.vessels
            assert baseline_co2_data['helicopters'] == baseline_co2.helicopters
            assert baseline_co2_data['materials'] == baseline_co2.materials
            assert baseline_co2_data['external_energy_supply'] == baseline_co2.external_energy_supply

        expected_baseline_nox_entries = [
            {
                "datetime": planned_start_datetime,
                "planned_step": step_1,
                **mock_baseline_nox_data,
            },
            {
                "datetime": planned_start_datetime + datetime.timedelta(days=0.5),
                "planned_step": step_2,
                **mock_baseline_nox_data,
            },
            {
                "datetime": planned_start_datetime + datetime.timedelta(days=0.75),
                "planned_step": step_3,
                **mock_baseline_nox_data,
            },
            {
                "datetime": planned_start_datetime + datetime.timedelta(days=1.0),
                "planned_step": step_4,
                **multiply_baseline_nox(baseline=mock_baseline_nox_data, multiplier=0.8),
            },
            {
                "datetime": planned_start_datetime + datetime.timedelta(days=2.0),
                "planned_step": step_4,
                **multiply_baseline_nox(baseline=mock_baseline_nox_data, multiplier=0.2),
            },
            {
                "datetime": planned_start_datetime + datetime.timedelta(days=2.25),
                "planned_step": step_5,
                **multiply_baseline_nox(baseline=mock_baseline_nox_data, multiplier=0.75),
            },
            {
                "datetime": planned_start_datetime + datetime.timedelta(days=3.0),
                "planned_step": step_5,
                **multiply_baseline_nox(baseline=mock_baseline_nox_data, multiplier=0.25),
            },
        ]

        for baseline_nox_data, baseline_nox in zip(
            expected_baseline_nox_entries,
            BaselineNOX.objects.filter(planned_step__well_planner=well_plan).order_by('datetime'),
        ):
            assert baseline_nox_data['planned_step'] == baseline_nox.planned_step
            assert baseline_nox_data['datetime'] == baseline_nox.datetime
            assert baseline_nox_data['asset'] == baseline_nox.asset
            assert baseline_nox_data['vessels'] == baseline_nox.vessels
            assert baseline_nox_data['helicopters'] == baseline_nox.helicopters
            assert baseline_nox_data['external_energy_supply'] == baseline_nox.external_energy_supply


@pytest.mark.django_db
class TestCalculateTargets:
    @pytest.fixture
    def mock_target_co2_data(self) -> TargetCO2Data:
        mock_target_co2 = TargetCO2Data(
            asset=10000,
            boilers=20000,
            vessels=30000,
            helicopters=40000,
            materials=50000,
            external_energy_supply=60000,
            emission_reduction_initiatives=[],
        )
        return mock_target_co2

    @pytest.fixture
    def mock_calculate_planned_step_target_co2(
        self, mocker: MockerFixture, mock_target_co2_data: TargetCO2Data
    ) -> MagicMock:
        mock_calculate_planned_step_target_co2 = mocker.patch(
            "apps.emissions.services.wells.calculate_planned_step_target_co2"
        )
        mock_calculate_planned_step_target_co2.return_value = mock_target_co2_data
        return mock_calculate_planned_step_target_co2

    @pytest.fixture
    def mock_target_nox_data(self) -> TargetCO2Data:
        mock_target_nox = TargetNOXData(
            asset=100000,
            boilers=200000,
            vessels=300000,
            helicopters=400000,
            external_energy_supply=600000,
            emission_reduction_initiatives=[],
        )
        return mock_target_nox

    @pytest.fixture
    def mock_calculate_planned_step_target_nox(
        self, mocker: MockerFixture, mock_target_nox_data: TargetCO2Data
    ) -> MagicMock:
        mock_calculate_planned_step_target_nox = mocker.patch(
            "apps.emissions.services.wells.calculate_planned_step_target_nox"
        )
        mock_calculate_planned_step_target_nox.return_value = mock_target_nox_data
        return mock_calculate_planned_step_target_nox

    def test_should_calculate_targets(
        self,
        mock_target_co2_data: TargetCO2Data,
        mock_target_nox_data: TargetNOXData,
        mock_calculate_planned_step_target_nox: MagicMock,
        mock_calculate_planned_step_target_co2: MagicMock,
    ):
        planned_start_datetime = datetime.datetime(2021, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
        well_plan = WellPlannerFactory(planned_start_date=planned_start_datetime)

        step_1 = WellPlannerPlannedStepFactory(well_planner=well_plan, improved_duration=0.5)
        step_2 = WellPlannerPlannedStepFactory(well_planner=well_plan, improved_duration=0.25)
        step_3 = WellPlannerPlannedStepFactory(well_planner=well_plan, improved_duration=0.25)
        step_4 = WellPlannerPlannedStepFactory(well_planner=well_plan, improved_duration=1.25)
        step_5 = WellPlannerPlannedStepFactory(well_planner=well_plan, improved_duration=1.0)

        TargetCO2Factory(planned_step=step_1)
        TargetNOXFactory(planned_step=step_2)
        WellPlannerCompleteStepFactory(well_planner=well_plan)

        calculate_targets(well_plan=well_plan)

        expected_target_co2_entries = [
            {
                "datetime": planned_start_datetime,
                "planned_step": step_1,
                **mock_target_co2_data,
            },
            {
                "datetime": planned_start_datetime + datetime.timedelta(days=0.5),
                "planned_step": step_2,
                **mock_target_co2_data,
            },
            {
                "datetime": planned_start_datetime + datetime.timedelta(days=0.75),
                "planned_step": step_3,
                **mock_target_co2_data,
            },
            {
                "datetime": planned_start_datetime + datetime.timedelta(days=1.0),
                "planned_step": step_4,
                **multiply_target_co2(target=mock_target_co2_data, multiplier=0.8),
            },
            {
                "datetime": planned_start_datetime + datetime.timedelta(days=2.0),
                "planned_step": step_4,
                **multiply_target_co2(target=mock_target_co2_data, multiplier=0.2),
            },
            {
                "datetime": planned_start_datetime + datetime.timedelta(days=2.25),
                "planned_step": step_5,
                **multiply_target_co2(target=mock_target_co2_data, multiplier=0.75),
            },
            {
                "datetime": planned_start_datetime + datetime.timedelta(days=3.0),
                "planned_step": step_5,
                **multiply_target_co2(target=mock_target_co2_data, multiplier=0.25),
            },
        ]

        for target_co2_data, target_co2 in zip(
            expected_target_co2_entries,
            TargetCO2.objects.filter(planned_step__well_planner=well_plan).order_by('datetime'),
        ):
            assert target_co2_data['planned_step'] == target_co2.planned_step
            assert target_co2_data['datetime'] == target_co2.datetime
            assert target_co2_data['asset'] == target_co2.asset
            assert target_co2_data['vessels'] == target_co2.vessels
            assert target_co2_data['helicopters'] == target_co2.helicopters
            assert target_co2_data['materials'] == target_co2.materials
            assert target_co2_data['external_energy_supply'] == target_co2.external_energy_supply

            for emission_reduction_initiative_data, emission_reduction_initiative in zip(
                target_co2_data['emission_reduction_initiatives'],
                TargetCO2Reduction.objects.filter(target=target_co2).order_by('pk'),
            ):
                assert emission_reduction_initiative_data['value'] == emission_reduction_initiative.value

        expected_target_nox_entries = [
            {
                "datetime": planned_start_datetime,
                "planned_step": step_1,
                **mock_target_nox_data,
            },
            {
                "datetime": planned_start_datetime + datetime.timedelta(days=0.5),
                "planned_step": step_2,
                **mock_target_nox_data,
            },
            {
                "datetime": planned_start_datetime + datetime.timedelta(days=0.75),
                "planned_step": step_3,
                **mock_target_nox_data,
            },
            {
                "datetime": planned_start_datetime + datetime.timedelta(days=1.0),
                "planned_step": step_4,
                **multiply_target_nox(target=mock_target_nox_data, multiplier=0.8),
            },
            {
                "datetime": planned_start_datetime + datetime.timedelta(days=2.0),
                "planned_step": step_4,
                **multiply_target_nox(target=mock_target_nox_data, multiplier=0.2),
            },
            {
                "datetime": planned_start_datetime + datetime.timedelta(days=2.25),
                "planned_step": step_5,
                **multiply_target_nox(target=mock_target_nox_data, multiplier=0.75),
            },
            {
                "datetime": planned_start_datetime + datetime.timedelta(days=3.0),
                "planned_step": step_5,
                **multiply_target_nox(target=mock_target_nox_data, multiplier=0.25),
            },
        ]

        for target_nox_data, target_nox in zip(
            expected_target_nox_entries,
            TargetNOX.objects.filter(planned_step__well_planner=well_plan).order_by('datetime'),
        ):
            assert target_nox_data['planned_step'] == target_nox.planned_step
            assert target_nox_data['datetime'] == target_nox.datetime
            assert target_nox_data['asset'] == target_nox.asset
            assert target_nox_data['vessels'] == target_nox.vessels
            assert target_nox_data['helicopters'] == target_nox.helicopters
            assert target_nox_data['external_energy_supply'] == target_nox.external_energy_supply

            for emission_reduction_initiative_data, emission_reduction_initiative in zip(
                target_nox_data['emission_reduction_initiatives'],
                TargetNOXReduction.objects.filter(target=target_nox).order_by('pk'),
            ):
                assert emission_reduction_initiative_data['value'] == emission_reduction_initiative.value


@pytest.mark.django_db
@pytest.mark.parametrize('co2_factory, co2_model', ((BaselineCO2Factory, BaselineCO2), (TargetCO2Factory, TargetCO2)))
def test_get_co2_emissions(co2_factory: type[BaseCO2Factory], co2_model: type[BaseCO2]):
    well_plan = WellPlannerFactory()
    start = datetime.datetime(year=2022, month=1, day=1, hour=0, minute=0)
    co2_factory(
        planned_step__well_planner=well_plan,
        datetime=start,
    )
    co2_factory(
        planned_step__well_planner=well_plan,
        datetime=start + datetime.timedelta(hours=8),
    )
    co2_factory(
        planned_step__well_planner=well_plan,
        datetime=start + datetime.timedelta(days=1),
    )
    co2_factory(
        datetime=start,
    )

    emissions = get_co2_emissions(well_planner=well_plan, co2_model=co2_model).values(
        'date',
        'total_asset',
        'total_external_energy_supply',
        'total_vessels',
        'total_helicopters',
        'total_materials',
        'total_boilers',
    )

    assert list(emissions) == [
        {
            'date': datetime.date(2022, 1, 1),
            'total_asset': 5000.0,
            'total_external_energy_supply': 4.0,
            'total_helicopters': 40.0,
            'total_materials': 600.0,
            'total_vessels': 2000.0,
            'total_boilers': 100.0,
        },
        {
            'date': datetime.date(2022, 1, 2),
            'total_asset': 2500.0,
            'total_external_energy_supply': 2.0,
            'total_helicopters': 20.0,
            'total_materials': 300.0,
            'total_vessels': 1000.0,
            'total_boilers': 50.0,
        },
    ]


@pytest.mark.django_db
class TestCalculatePlannedEmissions:
    def test_calculate_planned_emissions(self, mocker: MockerFixture):
        mocked_calculate_baselines = mocker.patch("apps.emissions.services.wells.calculate_baselines")
        mocked_calculate_targets = mocker.patch("apps.emissions.services.wells.calculate_targets")

        well_plan = WellPlannerFactory(current_step=WellPlannerWizardStep.WELL_PLANNING)
        calculate_planned_emissions(well_plan)

        mocked_calculate_baselines.assert_called_once_with(well_plan=well_plan)
        mocked_calculate_targets.assert_called_once_with(well_plan=well_plan)

    @pytest.mark.parametrize(
        'current_step', (set(WellPlannerWizardStep.values) - {WellPlannerWizardStep.WELL_PLANNING})
    )
    def test_should_raise_error_for_invalid_current_step(self, current_step: WellPlannerWizardStep):
        well_planner = WellPlannerFactory(current_step=current_step)

        with pytest.raises(ValueError) as ex:
            calculate_planned_emissions(well_planner)

        assert str(ex.value) == "Unable to calculate planned emissions"


@pytest.mark.django_db
class TestGetEmissionReductions:
    @pytest.mark.parametrize(
        'improved_duration,reductions',
        (
            (0.5, [dict(date=datetime.date(2022, 6, 1), emission_reduction_initiatives=[])]),
            (1, [dict(date=datetime.date(2022, 6, 1), emission_reduction_initiatives=[])]),
            (
                1.5,
                [
                    dict(date=datetime.date(2022, 6, 1), emission_reduction_initiatives=[]),
                    dict(date=datetime.date(2022, 6, 2), emission_reduction_initiatives=[]),
                ],
            ),
        ),
    )
    def test_dates(self, improved_duration: float, reductions: list[EmissionReduction]):
        well_plan = WellPlannerFactory(planned_start_date=datetime.date(2022, 6, 1))
        WellPlannerPlannedStepFactory(improved_duration=improved_duration, well_planner=well_plan)

        assert get_emission_reductions(well_plan=well_plan, reduction_model=TargetCO2Reduction) == reductions

    def test_reductions(self):
        well_plan = WellPlannerFactory(planned_start_date=datetime.date(2022, 6, 1))
        baseload_eri = EmissionReductionInitiativeFactory(type=EmissionReductionInitiativeType.BASELOADS)
        power_system_eri = EmissionReductionInitiativeFactory(type=EmissionReductionInitiativeType.POWER_SYSTEMS)
        EmissionReductionInitiativeFactory()
        WellPlannerPlannedStepFactory(improved_duration=1.25, well_planner=well_plan)
        second_phase = WellPlannerPlannedStepFactory(improved_duration=0.5, well_planner=well_plan)
        third_phase = WellPlannerPlannedStepFactory(improved_duration=0.5, well_planner=well_plan)
        WellPlannerPlannedStepFactory(improved_duration=0.5)

        TargetCO2ReductionFactory(
            target__planned_step=second_phase,
            emission_reduction_initiative=baseload_eri,
            target__datetime=well_plan.planned_start_date + datetime.timedelta(days=1.25),
            value=30.5,
        )
        TargetCO2ReductionFactory(
            target__planned_step=second_phase,
            emission_reduction_initiative=power_system_eri,
            target__datetime=well_plan.planned_start_date + datetime.timedelta(days=1.25),
            value=13,
        )
        TargetCO2ReductionFactory(
            target__planned_step=third_phase,
            emission_reduction_initiative=baseload_eri,
            target__datetime=well_plan.planned_start_date + datetime.timedelta(days=1.75),
            value=9.5,
        )
        TargetCO2ReductionFactory(
            target__planned_step=third_phase,
            emission_reduction_initiative=baseload_eri,
            target__datetime=well_plan.planned_start_date + datetime.timedelta(days=2),
            value=10,
        )
        TargetCO2ReductionFactory(value=20, target__datetime=well_plan.planned_start_date)

        assert get_emission_reductions(well_plan=well_plan, reduction_model=TargetCO2Reduction) == [
            dict(date=datetime.date(2022, 6, 1), emission_reduction_initiatives=[]),
            dict(
                date=datetime.date(2022, 6, 2),
                emission_reduction_initiatives=[
                    dict(
                        date=datetime.date(2022, 6, 2),
                        emission_reduction_initiative=baseload_eri.pk,
                        emission_reduction_initiative__type=baseload_eri.type,
                        emission_reduction_initiative__name=baseload_eri.name,
                        total_value=40,
                    ),
                    dict(
                        date=datetime.date(2022, 6, 2),
                        emission_reduction_initiative=power_system_eri.pk,
                        emission_reduction_initiative__type=power_system_eri.type,
                        emission_reduction_initiative__name=power_system_eri.name,
                        total_value=13,
                    ),
                ],
            ),
            dict(
                date=datetime.date(2022, 6, 3),
                emission_reduction_initiatives=[
                    dict(
                        date=datetime.date(2022, 6, 3),
                        emission_reduction_initiative=baseload_eri.pk,
                        emission_reduction_initiative__type=baseload_eri.type,
                        emission_reduction_initiative__name=baseload_eri.name,
                        total_value=10,
                    )
                ],
            ),
        ]
