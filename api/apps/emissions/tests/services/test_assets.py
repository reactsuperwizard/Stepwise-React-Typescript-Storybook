import datetime

import pytest
from django.core.exceptions import ValidationError

from apps.emissions.consts import INITIAL_CONCEPT_MODES, INITIAL_CONCEPT_PHASES
from apps.emissions.factories import (
    AssetFactory,
    BaselineFactory,
    BaselineInputFactory,
    CompleteHelicopterUseFactory,
    CompleteVesselUseFactory,
    ConceptModeFactory,
    ConceptPhaseFactory,
    CustomModeFactory,
    CustomPhaseFactory,
    EmissionManagementPlanFactory,
    EmissionReductionInitiativeFactory,
    EmissionReductionInitiativeInputFactory,
    ExternalEnergySupplyFactory,
    HelicopterTypeFactory,
    MaterialTypeFactory,
    PlannedHelicopterUseFactory,
    PlannedVesselUseFactory,
    VesselTypeFactory,
)
from apps.emissions.factories.wells import WellCompleteStepMaterialFactory, WellPlannedStepMaterialFactory
from apps.emissions.models import (
    Asset,
    AssetSeason,
    AssetType,
    Baseline,
    BaselineInput,
    CustomMode,
    CustomPhase,
    EmissionManagementPlan,
    EmissionReductionInitiative,
    EmissionReductionInitiativeInput,
    EmissionReductionInitiativeType,
    MaterialCategory,
)
from apps.emissions.services import (
    BaselineInputData,
    BaselineSeasonData,
    EmissionReductionInitiativeInputData,
    activate_baseline,
    activate_emission_management_plan,
    baseline_modes,
    baseline_phases,
    create_asset,
    create_baseline,
    create_custom_mode,
    create_custom_phase,
    create_emission_management_plan,
    create_emission_reduction_initiative,
    create_helicopter_type,
    create_initial_concept_modes,
    create_initial_concept_phases,
    create_material_type,
    create_vessel_type,
    delete_asset,
    delete_baseline,
    delete_emission_management_plan,
    delete_emission_reduction_initiative,
    delete_helicopter_type,
    delete_material_type,
    delete_vessel_type,
    duplicate_asset,
    duplicate_baseline,
    duplicate_emission_management_plan,
    update_asset,
    update_baseline,
    update_custom_mode,
    update_custom_phase,
    update_emission_management_plan,
    update_emission_reduction_initiative,
    update_helicopter_type,
    update_material_type,
    update_vessel_type,
)
from apps.emissions.services.assets import (
    get_complete_assets,
    validate_baseline_data,
    validate_emission_reduction_initiative_data,
)
from apps.kims.factories import VesselFactory
from apps.tenants.factories import TenantFactory, UserFactory
from apps.wells.factories import WellPlannerFactory


@pytest.fixture
def helicopter_type_data() -> dict:
    return {
        "type": "Helicopter Type",
        "fuel_density": 1,
        "co2_per_fuel": 2,
        "nox_per_fuel": 3,
        "fuel_consumption": 4,
        "fuel_cost": 5,
        "co2_tax": 6,
        "nox_tax": 7,
    }


@pytest.mark.django_db
def test_get_complete_assets():
    tenant = TenantFactory()
    first_asset = AssetFactory(tenant=tenant, draft=False)
    first_baseline = BaselineFactory(active=True, asset=first_asset)
    BaselineFactory(active=False, asset=first_asset)
    EmissionManagementPlanFactory(active=False, baseline=first_baseline)
    BaselineFactory(active=True, asset__draft=False)
    BaselineFactory()
    AssetFactory(tenant=tenant, draft=True)
    second_asset = AssetFactory(tenant=tenant, draft=False)
    second_baseline = BaselineFactory(active=False, asset=second_asset)
    third_baseline = BaselineFactory(active=True, asset=second_asset)
    EmissionManagementPlanFactory(active=True, baseline=second_baseline)
    third_emission_management_plan = EmissionManagementPlanFactory(active=True, baseline=third_baseline)
    EmissionManagementPlanFactory()

    complete_assets = list(get_complete_assets(tenant))

    assert len(complete_assets) == 2

    assert complete_assets[0].pk == first_asset.pk
    assert complete_assets[0].active_baseline == first_baseline.name
    assert complete_assets[0].active_emission_management_plan is None

    assert complete_assets[1].pk == second_asset.pk
    assert complete_assets[1].active_baseline == third_baseline.name
    assert complete_assets[1].active_emission_management_plan == third_emission_management_plan.name


@pytest.mark.django_db
class TestCreateAsset:
    @pytest.fixture
    def asset_data(self):
        return {
            "name": "Asset",
            "type": AssetType.SEMI,
            "design_description": "Design description",
            "green_house_gas_class_notation": "Green house gas",
        }

    @pytest.fixture
    def external_energy_supply_data(self):
        return {
            "type": "External energy supply",
            "capacity": 1,
            "co2": 2,
            "nox": 3,
            "generator_efficiency_factor": 4,
        }

    def test_create_asset(self, asset_data: dict, external_energy_supply_data: dict):
        data = {**asset_data, "external_energy_supply": external_energy_supply_data}
        tenant = TenantFactory()
        user = UserFactory()
        concept_phases = ConceptPhaseFactory.create_batch(2, tenant=tenant)
        ConceptPhaseFactory()
        ConceptModeFactory(tenant=tenant, asset_types=[AssetType.DRILLSHIP])
        concept_modes = [
            ConceptModeFactory(tenant=tenant, asset_types=[AssetType.FIXED_PLATFORM, AssetType.SEMI]),
            ConceptModeFactory(tenant=tenant, asset_types=[AssetType.SEMI, AssetType.JACKUP]),
        ]
        ConceptModeFactory()

        asset = create_asset(tenant=tenant, user=user, **data)

        assert asset.tenant == tenant
        assert asset.draft is True
        assert asset.deleted is False
        assert asset.vessel is None

        for key, value in asset_data.items():
            assert getattr(asset, key) == value

        external_energy_supply = asset.external_energy_supply
        for key, value in external_energy_supply_data.items():
            assert getattr(external_energy_supply, key) == value

        assert asset.customphase_set.count() == 2

        custom_phase_1, custom_phase_2 = asset.customphase_set.all().order_by('id')

        for index, custom_phase in enumerate([custom_phase_1, custom_phase_2]):
            assert custom_phase.name == concept_phases[index].name
            assert custom_phase.description == concept_phases[index].description
            assert custom_phase.phase == concept_phases[index]

        assert asset.custommode_set.count() == 2

        custom_mode_1, custom_mode_2 = asset.custommode_set.all().order_by('id')

        for index, custom_mode in enumerate([custom_mode_1, custom_mode_2]):
            assert custom_mode.name == concept_modes[index].name
            assert custom_mode.description == concept_modes[index].description
            assert custom_mode.mode == concept_modes[index]

    def test_asset_name_must_be_unique(self, asset_data: dict, external_energy_supply_data: dict):
        data = {**asset_data, "external_energy_supply": external_energy_supply_data}
        tenant = TenantFactory()
        user = UserFactory()
        AssetFactory(name=asset_data['name'])

        with pytest.raises(ValidationError) as ex:
            create_asset(tenant=tenant, user=user, **data)
        assert ex.value.message_dict == {'name': ['Asset name is already used.']}

    def test_deleted_asset_name_is_no_longer_unique(self, asset_data: dict, external_energy_supply_data: dict):
        data = {**asset_data, "external_energy_supply": external_energy_supply_data}
        tenant = TenantFactory()
        user = UserFactory()
        AssetFactory.create_batch(2, name=asset_data['name'], deleted=True)

        create_asset(tenant=tenant, user=user, **data)

    def test_set_vessel(self, asset_data: dict, external_energy_supply_data: dict):
        data = {**asset_data, "external_energy_supply": external_energy_supply_data}
        tenant = TenantFactory()
        user = UserFactory()
        vessel = VesselFactory(name=asset_data["name"])

        asset = create_asset(tenant=tenant, user=user, **data)

        assert asset.vessel == vessel


@pytest.mark.django_db
class TestUpdateAsset:
    @pytest.fixture()
    def asset_data(self):
        return {
            "name": "Asset",
            "type": AssetType.SEMI,
            "design_description": "Design description",
            "green_house_gas_class_notation": "Green house gas",
            "draft": False,
        }

    @pytest.fixture()
    def external_energy_supply_data(self):
        return {
            "type": "External energy supply",
            "capacity": 1,
            "co2": 2,
            "nox": 3,
            "generator_efficiency_factor": 4,
        }

    @pytest.mark.parametrize('old_name,new_name', (('Old name', 'Old name'), ('Old name', 'New name')))
    def test_update_asset(self, old_name: str, new_name: str, asset_data: dict, external_energy_supply_data: dict):
        asset = AssetFactory(draft=True, name=old_name)
        BaselineFactory(asset=asset, draft=False, active=True)
        ExternalEnergySupplyFactory(asset=asset)
        user = UserFactory()
        asset_data = {**asset_data, "name": new_name}
        data = {**asset_data, "name": new_name, "external_energy_supply": external_energy_supply_data}

        updated_asset = update_asset(asset=asset, user=user, **data)
        updated_asset.refresh_from_db()

        for key, value in asset_data.items():
            assert getattr(updated_asset, key) == value

        assert updated_asset.vessel is None

        external_energy_supply = updated_asset.external_energy_supply
        for key, value in external_energy_supply_data.items():
            assert getattr(external_energy_supply, key) == value

    def test_asset_name_must_be_unique(self, asset_data: dict, external_energy_supply_data: dict):
        asset = AssetFactory(name="Old name")
        AssetFactory(name="New name")
        ExternalEnergySupplyFactory(asset=asset)
        user = UserFactory()
        asset_data = {**asset_data, "name": "New name"}
        data = {**asset_data, "external_energy_supply": external_energy_supply_data}

        with pytest.raises(ValidationError) as ex:
            update_asset(asset=asset, user=user, **data)
        assert ex.value.message_dict == {'name': ['Asset name is already used.']}

    def test_deleted_asset_name_is_no_longer_unique(self, asset_data: dict, external_energy_supply_data: dict):
        asset = AssetFactory(name="Old name")
        AssetFactory.build_batch(2, name="New name", deleted=True)
        ExternalEnergySupplyFactory(asset=asset)
        user = UserFactory()
        asset_data = {**asset_data, "name": "New name"}
        data = {**asset_data, "draft": True, "external_energy_supply": external_energy_supply_data}

        update_asset(asset=asset, user=user, **data)

    def test_set_vessel(self, asset_data: dict, external_energy_supply_data: dict):
        asset = AssetFactory(name="Old name")
        ExternalEnergySupplyFactory(asset=asset)
        vessel = VesselFactory(name=asset_data["name"])
        user = UserFactory()
        data = {**asset_data, "draft": True, "external_energy_supply": external_energy_supply_data}

        update_asset(asset=asset, user=user, **data)

        asset.refresh_from_db()

        assert asset.vessel == vessel

    def test_unable_to_change_status_without_active_baseline(self, asset_data: dict, external_energy_supply_data: dict):
        asset = AssetFactory(draft=True)
        ExternalEnergySupplyFactory(asset=asset)
        user = UserFactory()
        data = {**asset_data, "draft": False, "external_energy_supply": external_energy_supply_data}

        with pytest.raises(ValidationError) as ex:
            update_asset(asset=asset, user=user, **data)
        assert ex.value.message_dict == {'draft': ['Status cannot be changed without having an active baseline.']}


@pytest.mark.django_db
class TestDuplicateAsset:
    def test_duplicate_asset(self):
        user = UserFactory()
        asset = AssetFactory(
            name='Asset',
            type=AssetType.SEMI,
            vessel=VesselFactory(),
            design_description='Design',
            green_house_gas_class_notation='Green house gas class notation',
            draft=False,
        )
        external_energy_supply = ExternalEnergySupplyFactory(asset=asset)
        phase = CustomPhaseFactory(asset=asset)
        CustomPhaseFactory(asset=asset, phase=None)
        CustomPhaseFactory()
        mode = CustomModeFactory(asset=asset)
        CustomModeFactory(asset=asset, mode=None)
        CustomModeFactory()
        baseline = BaselineFactory(asset=asset)
        BaselineFactory(asset=asset, deleted=True)
        BaselineFactory()
        BaselineInputFactory(baseline=baseline, phase=phase, mode=mode)

        asset_copy = duplicate_asset(user=user, asset=asset)

        assert asset_copy.tenant == asset.tenant
        assert asset_copy.name == f'{asset.name} - Copy'
        assert asset_copy.type == asset.type
        assert asset_copy.design_description == asset.design_description
        assert asset_copy.green_house_gas_class_notation == asset.green_house_gas_class_notation
        assert asset_copy.draft is True
        assert asset_copy.vessel is None
        assert asset_copy.deleted is False

        external_energy_supply_copy = asset_copy.external_energy_supply
        assert external_energy_supply_copy.type == external_energy_supply.type
        assert external_energy_supply_copy.capacity == external_energy_supply.capacity
        assert external_energy_supply_copy.co2 == external_energy_supply.co2
        assert external_energy_supply_copy.nox == external_energy_supply.nox
        assert (
            external_energy_supply_copy.generator_efficiency_factor
            == external_energy_supply.generator_efficiency_factor
        )

        assert asset_copy.customphase_set.count() == 1
        assert asset_copy.customphase_set.get().phase == phase.phase
        assert asset_copy.custommode_set.count() == 1
        assert asset_copy.custommode_set.get().mode == mode.mode
        assert asset_copy.baselines.count() == 0

    def test_limit_name(self):
        user = UserFactory()
        asset = AssetFactory(name='x' * 255)
        ExternalEnergySupplyFactory(asset=asset)

        asset_copy = duplicate_asset(user=user, asset=asset)

        assert asset_copy.name == f'{asset.name[:248]} - Copy'

    @pytest.mark.freeze_time('2022-05-11')
    def test_asset_name_must_be_unique(self):
        user = UserFactory()
        asset = AssetFactory(name='Old name')
        ExternalEnergySupplyFactory(asset=asset)

        first_copy = duplicate_asset(user=user, asset=asset)

        assert first_copy.name == 'Old name - Copy'

        second_copy = duplicate_asset(user=user, asset=asset)

        assert second_copy.name == 'Old name - Copy - 11.05.2022 00:00:00'

        with pytest.raises(ValidationError) as ex:
            duplicate_asset(user=user, asset=asset)

        assert ex.value.messages == ["Unable to duplicate the asset."]


@pytest.mark.django_db
class TestDeleteAsset:
    def test_delete_asset(self):
        user = UserFactory()
        asset = AssetFactory(vessel=VesselFactory())
        WellPlannerFactory(asset=asset, deleted=True)
        WellPlannerFactory()

        assert asset.deleted is False

        delete_asset(asset=asset, user=user)

        asset.refresh_from_db()

        assert asset.deleted is True
        assert asset.vessel is None

    def test_unable_to_delete_asset_connected_to_well_plan(self):
        asset = AssetFactory()
        well_plan = WellPlannerFactory(asset=asset)
        user = UserFactory()

        with pytest.raises(ValidationError) as ex:
            delete_asset(asset=asset, user=user)
        assert (
            ex.value.message == f"Asset cannot be deleted right now. Asset is used by well plan \"{well_plan.name}\"."
        )


@pytest.mark.django_db
class TestActivateBaseline:
    def test_activate_baseline(self):
        user = UserFactory()
        asset = AssetFactory()
        old_active_baseline = BaselineFactory(active=True, draft=False, asset=asset)
        new_active_baseline = BaselineFactory(active=False, draft=False, asset=asset)
        unknown_active_baseline = BaselineFactory(active=True, draft=False)

        activate_baseline(baseline=new_active_baseline, user=user)

        old_active_baseline.refresh_from_db()
        new_active_baseline.refresh_from_db()
        unknown_active_baseline.refresh_from_db()

        assert old_active_baseline.active is False
        assert new_active_baseline.active is True
        assert unknown_active_baseline.active is True

    def test_unable_to_activate_draft_baseline(self):
        user = UserFactory()
        baseline = BaselineFactory(draft=True)

        with pytest.raises(ValidationError) as ex:
            activate_baseline(baseline=baseline, user=user)
        assert ex.value.message == "Only complete baselines can be activated."


@pytest.mark.django_db
class TestDeleteBaseline:
    def test_delete_baseline(self):
        user = UserFactory()
        baseline = BaselineFactory()

        assert baseline.deleted is False

        delete_baseline(baseline=baseline, user=user)

        baseline.refresh_from_db()

        assert baseline.deleted is True

    @pytest.mark.parametrize('asset_draft', (True, False))
    def test_delete_active_baseline(self, asset_draft: bool):
        user = UserFactory()
        asset = AssetFactory(draft=asset_draft)
        baseline = BaselineFactory(asset=asset, active=True)
        WellPlannerFactory(asset=asset, baseline=baseline, deleted=True)
        WellPlannerFactory(asset=asset)

        delete_baseline(baseline=baseline, user=user)

        baseline.refresh_from_db()
        asset.refresh_from_db()

        assert baseline.deleted is True
        assert baseline.active is False
        assert asset.draft is True

    def test_unable_to_delete_baseline_connected_to_well_plan(self):
        baseline = BaselineFactory(active=True)
        well_plan = WellPlannerFactory(asset=baseline.asset, baseline=baseline)
        user = UserFactory()

        with pytest.raises(ValidationError) as ex:
            delete_baseline(baseline=baseline, user=user)
        assert (
            ex.value.message
            == f"Baseline cannot be deleted right now. Baseline is used by well plan \"{well_plan.name}\"."
        )


@pytest.mark.django_db
class TestDuplicateBaseline:
    def test_duplicate_baseline(self):
        user = UserFactory()
        asset = AssetFactory()
        baseline = BaselineFactory(active=True, draft=False, asset=asset)
        baseline_input = BaselineInputFactory(baseline=baseline)

        baseline_copy = duplicate_baseline(user=user, baseline=baseline)

        assert baseline_copy.asset == asset
        assert baseline_copy.name == f'{baseline.name} - Copy'
        assert baseline_copy.description == baseline.description
        assert baseline_copy.boilers_fuel_consumption_summer == baseline.boilers_fuel_consumption_summer
        assert baseline_copy.boilers_fuel_consumption_winter == baseline.boilers_fuel_consumption_winter
        assert baseline_copy.active is False
        assert baseline_copy.draft is True

        baseline_input_copy = baseline_copy.baselineinput_set.get()

        assert baseline_input_copy.season == baseline_input.season
        assert baseline_input_copy.phase == baseline_input.phase
        assert baseline_input_copy.mode == baseline_input.mode
        assert baseline_input_copy.value == baseline_input.value

    def test_limit_name(self):
        user = UserFactory()
        baseline = BaselineFactory(name='x' * 255)

        baseline_copy = duplicate_baseline(user=user, baseline=baseline)

        assert baseline_copy.name == f'{"x" * 248} - Copy'

    @pytest.mark.freeze_time('2022-05-11')
    def test_baseline_name_must_be_unique(self):
        user = UserFactory()
        baseline = BaselineFactory(name='Old name')

        first_copy = duplicate_baseline(user=user, baseline=baseline)

        assert first_copy.name == 'Old name - Copy'

        second_copy = duplicate_baseline(user=user, baseline=baseline)

        assert second_copy.name == 'Old name - Copy - 11.05.2022 00:00:00'

        with pytest.raises(ValidationError) as ex:
            duplicate_baseline(user=user, baseline=baseline)

        assert ex.value.messages == ["Unable to duplicate the baseline."]


@pytest.mark.django_db
def test_create_initial_concept_phases():
    tenant = TenantFactory()

    create_initial_concept_phases(tenant=tenant)

    for name, description, transit in INITIAL_CONCEPT_PHASES:
        assert tenant.conceptphase_set.filter(name=name, description=description, transit=transit).exists()


@pytest.mark.django_db
def test_create_initial_concept_modes():
    tenant = TenantFactory()

    create_initial_concept_modes(tenant=tenant)

    for name, description, asset_types, transit in INITIAL_CONCEPT_MODES:
        assert tenant.conceptmode_set.filter(
            name=name, description=description, asset_types__contains=asset_types, transit=transit
        ).exists()


@pytest.mark.django_db
def test_create_custom_phase():
    user = UserFactory()
    asset = AssetFactory()

    data = {
        'asset': asset,
        'name': 'Custom Phase',
        'description': 'Custom Phase Description',
    }

    custom_phase = create_custom_phase(user=user, **data)

    for field, value in data.items():
        assert getattr(custom_phase, field) == value

    assert custom_phase.phase is None


@pytest.mark.django_db
class TestCreateCustomPhase:
    @pytest.fixture
    def data(self) -> dict:
        return {
            'asset': AssetFactory(),
            'name': 'Custom Phase',
            'description': 'Custom Phase Description',
        }

    def test_create_custom_phase(self, data: dict):
        user = UserFactory()
        CustomPhaseFactory(name=data['name'])

        custom_phase = create_custom_phase(user=user, **data)

        for field, value in data.items():
            assert getattr(custom_phase, field) == value

        assert custom_phase.phase is None

    def test_should_raise_for_custom_phase_with_existing_name(self, data: dict):
        user = UserFactory()
        CustomPhaseFactory(asset=data['asset'], name=data['name'])

        with pytest.raises(ValidationError) as ex:
            create_custom_phase(user=user, **data)

        assert ex.value.message == 'Phase with this name already exists.'


@pytest.mark.django_db
class TestUpdateCustomPhase:
    @pytest.fixture
    def data(self) -> dict:
        return {
            'name': 'Custom Phase',
            'description': 'Custom Phase Description',
        }

    def test_should_update_custom_phase(self, data: dict):
        user = UserFactory()
        custom_phase = CustomPhaseFactory(phase=None)

        update_custom_phase(custom_phase=custom_phase, user=user, **data)

        custom_phase.refresh_from_db()

        for field, value in data.items():
            assert getattr(custom_phase, field) == value

    def test_should_raise_for_custom_phase_with_concept_phase(self, data: dict):
        user = UserFactory()
        custom_phase = CustomPhaseFactory()

        with pytest.raises(ValidationError) as ex:
            update_custom_phase(custom_phase=custom_phase, user=user, **data)

        assert ex.value.message == 'Only custom phases can be updated.'

    def test_should_raise_for_custom_phase_with_existing_name(self, data: dict):
        user = UserFactory()
        custom_phase = CustomPhaseFactory(phase=None)
        CustomPhaseFactory(asset=custom_phase.asset, name=data['name'])

        with pytest.raises(ValidationError) as ex:
            update_custom_phase(custom_phase=custom_phase, user=user, **data)

        assert ex.value.message == 'Phase with this name already exists.'


@pytest.mark.django_db
class TestCreateCustomMode:
    @pytest.fixture
    def data(self) -> dict:
        return {
            'asset': AssetFactory(),
            'name': 'Custom Mode',
            'description': 'Custom Mode Description',
        }

    def test_create_custom_mode(self, data: dict):
        user = UserFactory()
        CustomModeFactory(name=data['name'])

        custom_mode = create_custom_mode(user=user, **data)

        for field, value in data.items():
            assert getattr(custom_mode, field) == value

        assert custom_mode.mode is None

    def test_should_raise_for_custom_mode_with_existing_name(self, data: dict):
        user = UserFactory()
        CustomModeFactory(asset=data['asset'], name=data['name'])

        with pytest.raises(ValidationError) as ex:
            create_custom_mode(user=user, **data)

        assert ex.value.message == 'Mode with this name already exists.'


@pytest.mark.django_db
class TestUpdateCustomMode:
    @pytest.fixture
    def data(self) -> dict:
        return {
            'name': 'Custom Mode',
            'description': 'Custom Mode Description',
        }

    def test_should_update_custom_mode(self, data: dict):
        user = UserFactory()
        custom_mode = CustomModeFactory(mode=None)

        update_custom_mode(custom_mode=custom_mode, user=user, **data)

        custom_mode.refresh_from_db()

        for field, value in data.items():
            assert getattr(custom_mode, field) == value

    def test_should_raise_for_custom_mode_with_concept_mode(self, data: dict):
        user = UserFactory()
        custom_mode = CustomModeFactory()

        with pytest.raises(ValidationError) as ex:
            update_custom_mode(custom_mode=custom_mode, user=user, **data)

        assert ex.value.message == 'Only custom modes can be updated.'

    def test_should_raise_for_custom_mode_with_existing_name(self, data: dict):
        user = UserFactory()
        custom_mode = CustomModeFactory(mode=None)
        CustomModeFactory(asset=custom_mode.asset, name=data['name'])

        with pytest.raises(ValidationError) as ex:
            update_custom_mode(custom_mode=custom_mode, user=user, **data)

        assert ex.value.message == 'Mode with this name already exists.'


@pytest.mark.django_db
class TestValidateBaselineData:
    @pytest.fixture
    def asset(self):
        return AssetFactory()

    @pytest.fixture(autouse=True)
    def transit_phase(self, asset: Asset) -> CustomPhase:
        return CustomPhaseFactory(asset=asset, phase__transit=True)

    @pytest.fixture(autouse=True)
    def transit_mode(self, asset: Asset) -> CustomMode:
        return CustomModeFactory(asset=asset, mode__transit=True)

    @pytest.fixture
    def mode(self, asset: Asset) -> CustomMode:
        mode = CustomModeFactory(asset=asset)
        return mode

    @pytest.fixture
    def phases(self, asset: Asset) -> tuple[CustomPhase, CustomPhase]:
        phases = CustomPhaseFactory.create_batch(2, asset=asset)
        return phases

    @pytest.fixture
    def summer_data(self, phases: tuple[CustomPhase, CustomPhase], mode: CustomMode) -> BaselineSeasonData:
        first_phase, second_phase = phases
        summer_data = BaselineSeasonData(
            transit=111.11,
            inputs=[
                BaselineInputData(
                    phase=first_phase,
                    mode=mode,
                    value=1,
                ),
                BaselineInputData(
                    phase=second_phase,
                    mode=mode,
                    value=2,
                ),
            ],
        )
        return summer_data

    @pytest.fixture
    def winter_data(self, phases: tuple[CustomPhase, CustomPhase], mode: CustomMode) -> BaselineSeasonData:
        first_phase, second_phase = phases
        winter_data = BaselineSeasonData(
            transit=222.22,
            inputs=[
                BaselineInputData(
                    phase=first_phase,
                    mode=mode,
                    value=3,
                ),
                BaselineInputData(
                    phase=second_phase,
                    mode=mode,
                    value=4,
                ),
            ],
        )
        return winter_data

    def test_should_validate(self, asset: Asset, summer_data: BaselineSeasonData, winter_data: BaselineSeasonData):
        validate_baseline_data(asset=asset, summer=summer_data, winter=winter_data)

    @pytest.mark.parametrize('season', ['summer', 'winter'])
    def test_should_raise_for_phase_from_another_asset(
        self, asset: Asset, summer_data: BaselineSeasonData, winter_data: BaselineSeasonData, season: str
    ):
        data = {
            'winter': winter_data,
            'summer': summer_data,
        }
        data[season]['inputs'][0]['phase'] = CustomPhaseFactory()

        with pytest.raises(ValidationError) as ex:
            validate_baseline_data(asset=asset, **data)

        assert ex.value.message == 'Chosen phase is not a valid choice.'

    @pytest.mark.parametrize('season', ['summer', 'winter'])
    def test_should_raise_for_mode_from_another_asset(
        self, asset: Asset, summer_data: BaselineSeasonData, winter_data: BaselineSeasonData, season: str
    ):
        data = {
            'winter': winter_data,
            'summer': summer_data,
        }
        data[season]['inputs'][0]['mode'] = CustomModeFactory()

        with pytest.raises(ValidationError) as ex:
            validate_baseline_data(asset=asset, **data)

        assert ex.value.message == 'Chosen mode is not a valid choice.'

    def test_should_raise_for_missing_season(
        self, asset: Asset, summer_data: BaselineSeasonData, winter_data: BaselineSeasonData
    ):
        del summer_data['inputs'][0]

        with pytest.raises(ValidationError) as ex:
            validate_baseline_data(asset=asset, summer=summer_data, winter=winter_data)

        assert ex.value.message == 'All baseline inputs are required.'

    def test_should_raise_for_missing_required_phases(
        self, asset: Asset, summer_data: BaselineSeasonData, winter_data: BaselineSeasonData
    ):
        CustomPhaseFactory(asset=asset)

        with pytest.raises(ValidationError) as ex:
            validate_baseline_data(asset=asset, summer=summer_data, winter=winter_data)

        assert ex.value.message == 'Provide all required phases.'

    def test_should_not_raise_for_custom_phases(
        self, asset: Asset, summer_data: BaselineSeasonData, winter_data: BaselineSeasonData
    ):
        CustomPhaseFactory(asset=asset, phase=None)

        validate_baseline_data(asset=asset, summer=summer_data, winter=winter_data)

    def test_should_raise_for_missing_mode(self, asset: Asset):
        with pytest.raises(ValidationError) as ex:
            validate_baseline_data(
                asset=asset,
                summer=BaselineSeasonData(transit=0, inputs=[]),
                winter=BaselineSeasonData(transit=0, inputs=[]),
            )

        assert ex.value.message == 'Add at least one mode.'

    def test_should_raise_for_transit_phase(
        self,
        asset: Asset,
        summer_data: BaselineSeasonData,
        winter_data: BaselineSeasonData,
        transit_phase: CustomPhase,
        mode: CustomMode,
    ):
        transit_phase_input_data = BaselineInputData(
            phase=transit_phase,
            mode=mode,
            value=1,
        )
        summer_data['inputs'].append(transit_phase_input_data)
        winter_data['inputs'].append(transit_phase_input_data)

        with pytest.raises(ValidationError) as ex:
            validate_baseline_data(asset=asset, summer=summer_data, winter=winter_data)

        assert ex.value.message == 'Chosen phase is not a valid choice.'

    def test_should_raise_for_transit_mode(
        self,
        asset: Asset,
        summer_data: BaselineSeasonData,
        winter_data: BaselineSeasonData,
        transit_mode: CustomMode,
        phases: tuple[CustomPhase, CustomPhase],
    ):
        phase, _ = phases
        transit_mode_input_data = BaselineInputData(
            phase=phase,
            mode=transit_mode,
            value=1,
        )
        summer_data['inputs'].append(transit_mode_input_data)
        winter_data['inputs'].append(transit_mode_input_data)

        with pytest.raises(ValidationError) as ex:
            validate_baseline_data(asset=asset, summer=summer_data, winter=winter_data)

        assert ex.value.message == 'Chosen mode is not a valid choice.'


@pytest.mark.django_db
class TestCreateBaseline:
    @pytest.fixture
    def asset(self):
        return AssetFactory()

    @pytest.fixture(autouse=True)
    def transit_phase(self, asset: Asset) -> CustomPhase:
        return CustomPhaseFactory(asset=asset, phase__transit=True)

    @pytest.fixture(autouse=True)
    def transit_mode(self, asset: Asset) -> CustomMode:
        return CustomModeFactory(asset=asset, mode__transit=True)

    @pytest.fixture
    def data(self, asset: Asset) -> dict:
        return {
            "asset": asset,
            "name": "Test baseline",
            "description": "Test description",
            "boilers_fuel_consumption_summer": 13,
            "boilers_fuel_consumption_winter": 7.5,
            "draft": True,
        }

    @pytest.fixture
    def mode(self, asset: Asset) -> CustomMode:
        mode = CustomModeFactory(asset=asset)
        return mode

    @pytest.fixture
    def phases(self, asset: Asset) -> tuple[CustomPhase, CustomPhase]:
        phases = CustomPhaseFactory.create_batch(2, asset=asset)
        return phases

    @pytest.fixture
    def summer_data(self, phases: tuple[CustomPhase, CustomPhase], mode: CustomMode) -> BaselineSeasonData:
        first_phase, second_phase = phases
        summer_data = BaselineSeasonData(
            transit=111.11,
            inputs=[
                BaselineInputData(
                    phase=first_phase,
                    mode=mode,
                    value=1,
                ),
                BaselineInputData(
                    phase=second_phase,
                    mode=mode,
                    value=2,
                ),
            ],
        )
        return summer_data

    @pytest.fixture
    def winter_data(self, phases: tuple[CustomPhase, CustomPhase], mode: CustomMode) -> BaselineSeasonData:
        first_phase, second_phase = phases
        winter_data = BaselineSeasonData(
            transit=222.22,
            inputs=[
                BaselineInputData(
                    phase=first_phase,
                    mode=mode,
                    value=3,
                ),
                BaselineInputData(
                    phase=second_phase,
                    mode=mode,
                    value=4,
                ),
            ],
        )
        return winter_data

    def test_should_create_baseline(
        self,
        data: dict,
        winter_data: BaselineSeasonData,
        summer_data: BaselineSeasonData,
        transit_phase: CustomPhase,
        transit_mode: CustomMode,
    ):
        user = UserFactory()

        baseline = create_baseline(user=user, summer=summer_data, winter=winter_data, **data)

        for field, value in data.items():
            assert getattr(baseline, field) == value

        for season, inputs in zip((AssetSeason.SUMMER, AssetSeason.WINTER), (summer_data, winter_data)):
            baseline_inputs = baseline.baselineinput_set.filter(season=season).order_by('id')

            for baseline_input, baseline_input_data in zip(baseline_inputs, inputs['inputs']):
                for field, value in baseline_input_data.items():
                    assert getattr(baseline_input, field) == value

        assert BaselineInput.objects.filter(
            baseline=baseline,
            phase=transit_phase,
            mode=transit_mode,
            season=AssetSeason.SUMMER,
            value=summer_data['transit'],
        ).exists()
        assert BaselineInput.objects.filter(
            baseline=baseline,
            phase=transit_phase,
            mode=transit_mode,
            season=AssetSeason.WINTER,
            value=winter_data['transit'],
        ).exists()

    def test_baseline_name_is_already_used(
        self, asset: Asset, data: dict, winter_data: BaselineSeasonData, summer_data: BaselineSeasonData
    ):
        BaselineFactory(draft=False, asset=asset, name=data["name"])
        user = UserFactory()

        with pytest.raises(ValidationError) as ex:
            create_baseline(user=user, winter=winter_data, summer=summer_data, **data)
        assert ex.value.message_dict == {'name': ['Baseline name is already used.']}

    def test_baseline_name_is_unique_per_asset(
        self, asset: Asset, data: dict, winter_data: BaselineSeasonData, summer_data: BaselineSeasonData
    ):
        user = UserFactory()
        BaselineFactory.create_batch(2, name=data["name"], deleted=True, asset=asset)
        BaselineFactory(name=data["name"])

        create_baseline(user=user, summer=summer_data, winter=winter_data, **data)


@pytest.mark.django_db
class TestUpdateBaseline:
    @pytest.fixture
    def data(self) -> dict:
        return {
            "name": "Test baseline",
            "description": "Test description",
            "boilers_fuel_consumption_summer": 13,
            "boilers_fuel_consumption_winter": 7.5,
            "draft": True,
        }

    @pytest.fixture
    def asset(self) -> Asset:
        return AssetFactory()

    @pytest.fixture
    def transit_phase(self, asset: Asset) -> CustomPhase:
        return CustomPhaseFactory(asset=asset, phase__transit=True)

    @pytest.fixture
    def transit_mode(self, asset: Asset) -> CustomMode:
        return CustomModeFactory(asset=asset, mode__transit=True)

    @pytest.fixture
    def mode(self, asset: Asset) -> CustomMode:
        mode = CustomModeFactory(asset=asset)
        return mode

    @pytest.fixture
    def baseline(
        self, asset: Asset, transit_phase: CustomPhase, transit_mode: CustomMode, mode: CustomMode
    ) -> Baseline:
        baseline = BaselineFactory(asset=asset)
        BaselineInputFactory(baseline=baseline, phase=transit_phase, mode=transit_mode, value=100)

        return baseline

    @pytest.fixture
    def phases(self, asset: Asset) -> tuple[CustomPhase, CustomPhase]:
        phases = CustomPhaseFactory.create_batch(2, asset=asset)
        return phases

    @pytest.fixture
    def emission_reduction_initiative(self, baseline: Baseline) -> EmissionReductionInitiative:
        emission_reduction__initiative = EmissionReductionInitiativeFactory(emission_management_plan__baseline=baseline)
        return emission_reduction__initiative

    @pytest.fixture
    def optional_baseline_inputs(
        self, asset: Asset, baseline: Baseline, mode: CustomMode
    ) -> tuple[BaselineInput, BaselineInput]:
        optional_phase = CustomPhaseFactory(asset=asset, phase=None)
        summer_optional_baseline_input = BaselineInputFactory(
            baseline=baseline, phase=optional_phase, mode=mode, season=AssetSeason.SUMMER
        )
        winter_optional_baseline_input = BaselineInputFactory(
            baseline=baseline, phase=optional_phase, mode=mode, season=AssetSeason.WINTER
        )

        return summer_optional_baseline_input, winter_optional_baseline_input

    @pytest.fixture
    def summer_data(
        self, baseline: Baseline, phases: tuple[CustomPhase, CustomPhase], mode: CustomMode
    ) -> BaselineSeasonData:
        first_phase, second_phase = phases
        BaselineInputFactory(phase=first_phase, mode=mode, season=AssetSeason.SUMMER, baseline=baseline, value=999)
        summer_data = BaselineSeasonData(
            transit=111.11,
            inputs=[
                BaselineInputData(
                    phase=first_phase,
                    mode=mode,
                    value=1,
                ),
                BaselineInputData(
                    phase=second_phase,
                    mode=mode,
                    value=2,
                ),
            ],
        )
        return summer_data

    @pytest.fixture
    def winter_data(
        self, baseline: Baseline, phases: tuple[CustomPhase, CustomPhase], mode: CustomMode
    ) -> BaselineSeasonData:
        first_phase, second_phase = phases
        BaselineInputFactory(phase=first_phase, mode=mode, season=AssetSeason.WINTER, baseline=baseline, value=999)
        winter_data = BaselineSeasonData(
            transit=222.22,
            inputs=[
                BaselineInputData(
                    phase=first_phase,
                    mode=mode,
                    value=3,
                ),
                BaselineInputData(
                    phase=second_phase,
                    mode=mode,
                    value=4,
                ),
            ],
        )
        return winter_data

    @pytest.mark.parametrize('old_name,new_name', (('Old name', 'Old name'), ('Old name', 'New name')))
    def test_should_update_baseline(
        self,
        old_name: str,
        new_name: str,
        baseline: Baseline,
        winter_data: BaselineSeasonData,
        summer_data: BaselineSeasonData,
        data: dict,
        transit_phase: CustomPhase,
        transit_mode: CustomMode,
        phases: tuple[CustomPhase, CustomPhase],
        emission_reduction_initiative: EmissionReductionInitiative,
        mode: CustomMode,
    ):
        user = UserFactory()
        baseline.name = old_name
        baseline.save()

        data = {**data, 'name': new_name}
        update_baseline(baseline=baseline, user=user, summer=summer_data, winter=winter_data, **data)

        baseline.refresh_from_db()

        for field, value in data.items():
            assert getattr(baseline, field) == value

        for season, inputs in zip((AssetSeason.SUMMER, AssetSeason.WINTER), (summer_data, winter_data)):
            baseline_inputs = baseline.baselineinput_set.inputs().filter(season=season).order_by('id')

            for baseline_input, baseline_input_data in zip(baseline_inputs, inputs['inputs']):
                for field, value in baseline_input_data.items():
                    assert getattr(baseline_input, field) == value

        assert BaselineInput.objects.filter(
            baseline=baseline,
            phase=transit_phase,
            mode=transit_mode,
            season=AssetSeason.SUMMER,
            value=summer_data['transit'],
        ).exists()
        assert BaselineInput.objects.filter(
            baseline=baseline,
            phase=transit_phase,
            mode=transit_mode,
            season=AssetSeason.WINTER,
            value=winter_data['transit'],
        ).exists()

        _, second_phase = phases

        assert EmissionReductionInitiativeInput.objects.filter(
            emission_reduction_initiative=emission_reduction_initiative,
            phase=second_phase,
            mode=mode,
            value=0,
        ).exists()

    @pytest.mark.parametrize('asset_draft', (True, False))
    def test_should_make_baseline_inactive(
        self,
        asset_draft: bool,
        asset: Asset,
        data: dict,
        winter_data: BaselineSeasonData,
        summer_data: BaselineSeasonData,
    ):
        user = UserFactory()
        baseline = BaselineFactory(asset=asset, draft=False, active=True)

        update_baseline(baseline=baseline, user=user, summer=summer_data, winter=winter_data, **data)

        baseline.refresh_from_db()
        asset.refresh_from_db()

        assert baseline.draft is True
        assert baseline.active is False

        assert asset.draft is True

    def test_should_not_raise_when_removing_inputs_in_an_unused_baseline(
        self,
        baseline: Baseline,
        data: dict,
        winter_data: BaselineSeasonData,
        summer_data: BaselineSeasonData,
        optional_baseline_inputs: tuple[BaselineInput, BaselineInput],
    ):
        user = UserFactory()
        update_baseline(baseline=baseline, user=user, summer=summer_data, winter=winter_data, **data)

        summer_optional_baseline_input, winter_optional_baseline_input = optional_baseline_inputs

        assert BaselineInput.objects.filter(pk=summer_optional_baseline_input.pk).exists() is False
        assert BaselineInput.objects.filter(pk=winter_optional_baseline_input.pk).exists() is False

    def test_should_raise_when_removing_inputs_in_a_used_baseline(
        self,
        baseline: Baseline,
        data: dict,
        winter_data: BaselineSeasonData,
        summer_data: BaselineSeasonData,
        emission_reduction_initiative: EmissionReductionInitiative,
        optional_baseline_inputs: tuple[BaselineInput, BaselineInput],
    ):
        user = UserFactory()

        with pytest.raises(ValidationError) as ex:
            update_baseline(baseline=baseline, user=user, summer=summer_data, winter=winter_data, **data)

        assert ex.value.message == "Inputs can not be removed in a used baseline."

        summer_optional_baseline_input, winter_optional_baseline_input = optional_baseline_inputs

        assert BaselineInput.objects.filter(pk=summer_optional_baseline_input.pk).exists() is True
        assert BaselineInput.objects.filter(pk=winter_optional_baseline_input.pk).exists() is True

    def test_baseline_name_is_already_used(
        self,
        asset: Asset,
        baseline: Baseline,
        data: dict,
        winter_data: BaselineSeasonData,
        summer_data: BaselineSeasonData,
    ):
        user = UserFactory()
        BaselineFactory(name=data["name"], asset=asset)

        with pytest.raises(ValidationError) as ex:
            update_baseline(baseline=baseline, user=user, summer=summer_data, winter=winter_data, **data)
        assert ex.value.message_dict == {'name': ['Baseline name is already used.']}

    def test_baseline_name_is_unique_per_asset(
        self,
        asset: Asset,
        baseline: Baseline,
        data: dict,
        summer_data: BaselineSeasonData,
        winter_data: BaselineSeasonData,
    ):
        user = UserFactory()
        BaselineFactory.create_batch(2, name=data["name"], deleted=True, asset=asset)
        BaselineFactory(name=data["name"])

        update_baseline(baseline=baseline, user=user, summer=summer_data, winter=winter_data, **data)


@pytest.mark.django_db
def test_create_vessel_type():
    user = UserFactory()
    tenant = TenantFactory()
    data = {
        "type": "Anchor handling tug supply vessel (AHTS)",
        "fuel_type": "Fuel type",
        "fuel_density": 1.0,
        "co2_per_fuel": 2.0,
        "nox_per_fuel": 3.0,
        "co2_tax": 4.0,
        "nox_tax": 5.0,
        "fuel_cost": 6.0,
        "fuel_consumption_summer": 4.9,
        "fuel_consumption_winter": 5.5,
        "tenant": tenant,
    }
    vessel_type = create_vessel_type(user=user, **data)
    vessel_type.refresh_from_db()

    for key, value in data.items():
        assert getattr(vessel_type, key) == value
    assert vessel_type.deleted is False


@pytest.mark.django_db
def test_update_vessel_type():
    user = UserFactory()
    vessel_type = VesselTypeFactory()
    data = {
        "type": "Anchor handling tug supply vessel (AHTS)",
        "fuel_type": "Fuel type",
        "fuel_density": 1.0,
        "co2_per_fuel": 2.0,
        "nox_per_fuel": 3.0,
        "co2_tax": 4.0,
        "nox_tax": 5.0,
        "fuel_cost": 6.0,
        "fuel_consumption_summer": 4.9,
        "fuel_consumption_winter": 5.5,
    }
    vessel_type = update_vessel_type(user=user, vessel_type=vessel_type, **data)
    vessel_type.refresh_from_db()

    for key, value in data.items():
        assert getattr(vessel_type, key) == value


@pytest.mark.django_db
@pytest.mark.parametrize('vessel_use_factory', (PlannedVesselUseFactory, CompleteVesselUseFactory))
class TestDeleteVesselType:
    def test_delete_vessel_type(self, vessel_use_factory: type[PlannedVesselUseFactory | CompleteVesselUseFactory]):
        user = UserFactory()
        vessel_type = VesselTypeFactory()
        vessel_use_factory(vessel_type=vessel_type, well_planner__deleted=True)
        vessel_use_factory()

        assert vessel_type.deleted is False

        delete_vessel_type(vessel_type=vessel_type, user=user)

        vessel_type.refresh_from_db()

        assert vessel_type.deleted is True

    def test_unable_to_delete_vessel_type_connected_to_well_plan(
        self, vessel_use_factory: type[PlannedVesselUseFactory | CompleteVesselUseFactory]
    ):
        vessel_type = VesselTypeFactory()
        vessel_use = vessel_use_factory(vessel_type=vessel_type)
        user = UserFactory()

        with pytest.raises(ValidationError) as ex:
            delete_vessel_type(vessel_type=vessel_type, user=user)
        assert (
            ex.value.message
            == f"Vessel type cannot be deleted right now. Vessel type is used by well plan \"{vessel_use.well_planner.name}\"."
        )


@pytest.mark.django_db
class TestValidateEmissionReductionInitiativeData:
    def test_should_validate_emission_reduction_initiative_data(self):
        asset = AssetFactory()
        phase_1, phase_2 = CustomPhaseFactory.create_batch(2, asset=asset)
        mode = CustomModeFactory(asset=asset)

        baseline = BaselineFactory(asset=asset)
        BaselineInputFactory(phase=phase_1, mode=mode, season=AssetSeason.WINTER, baseline=baseline, value=999)
        BaselineInputFactory(phase=phase_1, mode=mode, season=AssetSeason.SUMMER, baseline=baseline, value=999)
        BaselineInputFactory(phase=phase_2, mode=mode, season=AssetSeason.WINTER, baseline=baseline, value=999)
        BaselineInputFactory(phase=phase_2, mode=mode, season=AssetSeason.SUMMER, baseline=baseline, value=999)

        emission_management_plan = EmissionManagementPlanFactory(baseline=baseline)

        inputs = [
            EmissionReductionInitiativeInputData(
                phase=phase_1,
                mode=mode,
                value=1,
            ),
            EmissionReductionInitiativeInputData(
                phase=phase_2,
                mode=mode,
                value=2,
            ),
        ]

        validate_emission_reduction_initiative_data(emission_management_plan=emission_management_plan, inputs=inputs)

    def test_should_raise_for_invalid_phase(self):
        asset = AssetFactory()
        valid_phase = CustomPhaseFactory(asset=asset)
        invalid_phase = CustomPhaseFactory()
        mode_1, mode_2 = CustomModeFactory.create_batch(2, asset=asset)
        baseline = BaselineFactory(asset=asset)
        emission_management_plan = EmissionManagementPlanFactory(baseline=baseline)

        inputs = [
            EmissionReductionInitiativeInputData(
                phase=valid_phase,
                mode=mode_1,
                value=1,
            ),
            EmissionReductionInitiativeInputData(
                phase=valid_phase,
                mode=mode_2,
                value=1,
            ),
            EmissionReductionInitiativeInputData(
                phase=invalid_phase,
                mode=mode_1,
                value=2,
            ),
            EmissionReductionInitiativeInputData(
                phase=invalid_phase,
                mode=mode_2,
                value=2,
            ),
        ]

        with pytest.raises(ValidationError) as ex:
            validate_emission_reduction_initiative_data(
                emission_management_plan=emission_management_plan, inputs=inputs
            )

        assert ex.value.message == 'All energy reduction initiative inputs are required.'

    def test_should_raise_for_invalid_mode(self):
        asset = AssetFactory()
        phase_1, phase_2 = CustomPhaseFactory.create_batch(2, asset=asset)
        valid_mode = CustomModeFactory(asset=asset)
        invalid_mode = CustomModeFactory()

        baseline = BaselineFactory(asset=asset)
        BaselineInputFactory(phase=phase_1, mode=valid_mode, season=AssetSeason.SUMMER, baseline=baseline)
        BaselineInputFactory(phase=phase_2, mode=valid_mode, season=AssetSeason.SUMMER, baseline=baseline)

        emission_management_plan = EmissionManagementPlanFactory(baseline=baseline)

        inputs = [
            EmissionReductionInitiativeInputData(
                phase=phase_1,
                mode=valid_mode,
                value=1,
            ),
            EmissionReductionInitiativeInputData(
                phase=phase_2,
                mode=valid_mode,
                value=1,
            ),
            EmissionReductionInitiativeInputData(
                phase=phase_1,
                mode=invalid_mode,
                value=2,
            ),
            EmissionReductionInitiativeInputData(
                phase=phase_2,
                mode=invalid_mode,
                value=2,
            ),
        ]

        with pytest.raises(ValidationError) as ex:
            validate_emission_reduction_initiative_data(
                emission_management_plan=emission_management_plan, inputs=inputs
            )

        assert ex.value.message == 'All energy reduction initiative inputs are required.'

    def test_should_raise_for_missing_phase(self):
        asset = AssetFactory()
        phase_1, phase_2 = CustomPhaseFactory.create_batch(2, asset=asset)
        mode = CustomModeFactory(asset=asset)

        baseline = BaselineFactory(asset=asset)
        BaselineInputFactory(phase=phase_1, mode=mode, season=AssetSeason.SUMMER, baseline=baseline, value=999)
        BaselineInputFactory(phase=phase_2, mode=mode, season=AssetSeason.SUMMER, baseline=baseline, value=999)

        emission_management_plan = EmissionManagementPlanFactory(baseline=baseline)

        inputs = [
            EmissionReductionInitiativeInputData(
                phase=phase_1,
                mode=mode,
                value=1,
            ),
        ]

        with pytest.raises(ValidationError) as ex:
            validate_emission_reduction_initiative_data(
                emission_management_plan=emission_management_plan, inputs=inputs[:-1]
            )

        assert ex.value.message == 'All energy reduction initiative inputs are required.'

    def test_should_raise_for_missing_mode(self):
        asset = AssetFactory()
        phase = CustomPhaseFactory(asset=asset)
        mode_1, mode_2 = CustomModeFactory.create_batch(2, asset=asset)
        baseline = BaselineFactory(asset=asset)
        BaselineInputFactory(phase=phase, mode=mode_1, season=AssetSeason.SUMMER, baseline=baseline, value=999)
        BaselineInputFactory(phase=phase, mode=mode_2, season=AssetSeason.SUMMER, baseline=baseline, value=999)
        emission_management_plan = EmissionManagementPlanFactory(baseline=baseline)

        inputs = [
            EmissionReductionInitiativeInputData(
                phase=phase,
                mode=mode_1,
                value=1,
            ),
        ]

        with pytest.raises(ValidationError) as ex:
            validate_emission_reduction_initiative_data(
                emission_management_plan=emission_management_plan, inputs=inputs[:-1]
            )

        assert ex.value.message == 'All energy reduction initiative inputs are required.'


@pytest.mark.django_db
class TestCreateEmissionReductionInitiative:
    @pytest.fixture
    def asset(self) -> Asset:
        return AssetFactory()

    @pytest.fixture
    def transit_phase(self, asset: Asset) -> CustomPhase:
        transit_phase = CustomPhaseFactory(asset=asset, phase__transit=True)
        return transit_phase

    @pytest.fixture
    def transit_mode(self, asset: Asset) -> CustomMode:
        transit_mode = CustomModeFactory(asset=asset, mode__transit=True)
        return transit_mode

    @pytest.fixture
    def baseline(self, asset: Asset) -> Baseline:
        baseline = BaselineFactory(asset=asset)
        return baseline

    @pytest.fixture(autouse=True)
    def baseline_transit_input(
        self,
        baseline: Baseline,
        transit_phase: CustomPhase,
        transit_mode: CustomMode,
    ) -> BaselineInput:
        baseline_transit_input = BaselineInputFactory(
            phase=transit_phase, mode=transit_mode, season=AssetSeason.SUMMER, baseline=baseline, value=999
        )
        return baseline_transit_input

    @pytest.fixture
    def transit(self) -> float:
        return 999.99

    def test_should_create_emission_reduction_initiative(
        self, asset: Asset, baseline: Baseline, transit: float, baseline_transit_input: BaselineInput
    ):
        user = UserFactory()
        phase_1, phase_2 = CustomPhaseFactory.create_batch(2, asset=baseline.asset)
        mode = CustomModeFactory(asset=baseline.asset)
        BaselineInputFactory(baseline=baseline, phase=phase_1, mode=mode)
        BaselineInputFactory(baseline=baseline, phase=phase_2, mode=mode)
        emission_management_plan = EmissionManagementPlanFactory(baseline=baseline)
        WellPlannerFactory(emission_management_plan=emission_management_plan)

        data = {
            'emission_management_plan': emission_management_plan,
            'name': 'Test emission reduction initiative',
            'description': 'Test emission reduction initiative description',
            'vendor': 'Test emission reduction initiative vendor',
            'type': EmissionReductionInitiativeType.PRODUCTIVITY,
            "deployment_date": datetime.date(2022, 1, 14),
        }
        inputs_data = [
            EmissionReductionInitiativeInputData(
                phase=phase_1,
                mode=mode,
                value=1,
            ),
            EmissionReductionInitiativeInputData(
                phase=phase_2,
                mode=mode,
                value=2,
            ),
        ]
        EmissionReductionInitiativeFactory(
            name=data["name"],
            emission_management_plan=emission_management_plan,
            deleted=True,
        )
        EmissionReductionInitiativeFactory(
            name=data["name"],
            emission_management_plan__baseline__asset=asset,
            deleted=True,
        )
        EmissionReductionInitiativeFactory(
            name=data["name"],
            emission_management_plan__baseline=baseline,
            deleted=True,
        )
        EmissionReductionInitiativeFactory(
            name=data["name"],
            emission_management_plan__baseline__asset__tenant=asset.tenant,
            deleted=False,
        )
        EmissionReductionInitiativeFactory(
            name=data["name"],
            deleted=False,
        )
        emission_reduction_initiative = create_emission_reduction_initiative(
            user=user, inputs=inputs_data, transit=transit, **data
        )

        for field, value in data.items():
            assert getattr(emission_reduction_initiative, field) == value

        emission_reduction_initiative_inputs = (
            EmissionReductionInitiativeInput.objects.inputs()
            .filter(emission_reduction_initiative=emission_reduction_initiative)
            .order_by('pk')
        )

        for emission_reduction_initiative_input, emission_reduction_initiative_input_data in zip(
            emission_reduction_initiative_inputs,
            inputs_data,
        ):
            for field, value in emission_reduction_initiative_input_data.items():
                assert getattr(emission_reduction_initiative_input, field) == value

        assert EmissionReductionInitiativeInput.objects.filter(
            emission_reduction_initiative=emission_reduction_initiative,
            phase=baseline_transit_input.phase,
            mode=baseline_transit_input.mode,
            value=transit,
        ).exists()

    def test_should_raise_for_non_unique_name_in_relation_to_asset(self):
        asset = AssetFactory()
        user = UserFactory()
        emission_management_plan = EmissionManagementPlanFactory(baseline__asset=asset)
        emission_reduction_initiative = EmissionReductionInitiativeFactory(
            emission_management_plan__baseline__asset=asset, name='Test emission reduction initiative', deleted=False
        )

        with pytest.raises(ValidationError) as ex:
            create_emission_reduction_initiative(
                user=user,
                emission_management_plan=emission_management_plan,
                name=emission_reduction_initiative,
                description='Test emission reduction initiative description',
                type=EmissionReductionInitiativeType.PRODUCTIVITY,
                vendor='Test emission reduction initiative vendor',
                inputs=[],
                deployment_date=datetime.date(2022, 1, 14),
                transit=0,
            )

        assert ex.value.message_dict == {'name': ['Energy reduction initiative name is already used.']}


@pytest.mark.django_db
class TestUpdateEmissionReductionInitiative:
    @pytest.fixture
    def asset(self) -> Asset:
        return AssetFactory()

    @pytest.fixture
    def transit_phase(self, asset: Asset) -> CustomPhase:
        transit_phase = CustomPhaseFactory(asset=asset, phase__transit=True)
        return transit_phase

    @pytest.fixture
    def transit_mode(self, asset: Asset) -> CustomMode:
        transit_mode = CustomModeFactory(asset=asset, mode__transit=True)
        return transit_mode

    @pytest.fixture
    def baseline(self, asset: Asset) -> Baseline:
        baseline = BaselineFactory(asset=asset)
        return baseline

    @pytest.fixture
    def emission_reduction_initiative(
        self,
        baseline: Baseline,
    ) -> EmissionReductionInitiative:
        emission_reduction_initiative = EmissionReductionInitiativeFactory(emission_management_plan__baseline=baseline)
        return emission_reduction_initiative

    @pytest.fixture
    def transit(self) -> float:
        return 999.99

    @pytest.fixture
    def emission_reduction_initiative_transit_input(
        self,
        emission_reduction_initiative: EmissionReductionInitiative,
        transit: float,
        transit_phase: CustomPhase,
        transit_mode: CustomMode,
    ) -> EmissionReductionInitiativeInput:
        emission_reduction_initiative_transit_input = EmissionReductionInitiativeInputFactory(
            emission_reduction_initiative=emission_reduction_initiative,
            phase=transit_phase,
            mode=transit_mode,
            value=0,
        )

        assert transit != emission_reduction_initiative_transit_input.value
        return emission_reduction_initiative_transit_input

    def test_should_update_emission_reduction_initiative(
        self,
        baseline: Baseline,
        emission_reduction_initiative: EmissionReductionInitiative,
        emission_reduction_initiative_transit_input: EmissionReductionInitiativeInput,
        transit: float,
    ):
        asset = AssetFactory()
        user = UserFactory()
        phase_1, phase_2 = CustomPhaseFactory.create_batch(2, asset=asset)
        mode = CustomModeFactory(asset=asset)
        BaselineInputFactory(baseline=baseline, phase=phase_1, mode=mode)
        BaselineInputFactory(baseline=baseline, phase=phase_2, mode=mode)
        EmissionReductionInitiativeInputFactory(
            emission_reduction_initiative=emission_reduction_initiative, phase=phase_1, mode=mode, value=9999
        )
        EmissionReductionInitiativeInputFactory(
            emission_reduction_initiative=emission_reduction_initiative, phase=phase_2, mode=mode, value=9999
        )
        WellPlannerFactory(
            emission_management_plan=emission_reduction_initiative.emission_management_plan, baseline=baseline
        )

        data = {
            'name': 'Test emission reduction initiative',
            'description': 'Test emission reduction initiative description',
            'vendor': 'Test emission reduction initiative vendor',
            'type': EmissionReductionInitiativeType.PRODUCTIVITY,
            "deployment_date": datetime.date(2022, 1, 14),
        }
        inputs_data = [
            EmissionReductionInitiativeInputData(
                phase=phase_1,
                mode=mode,
                value=1,
            ),
            EmissionReductionInitiativeInputData(
                phase=phase_2,
                mode=mode,
                value=2,
            ),
        ]
        EmissionReductionInitiativeFactory(
            name=data["name"],
            emission_management_plan=emission_reduction_initiative.emission_management_plan,
            deleted=True,
        )
        EmissionReductionInitiativeFactory(
            name=data["name"],
            emission_management_plan__baseline__asset=asset,
            deleted=True,
        )
        EmissionReductionInitiativeFactory(
            name=data["name"],
            emission_management_plan__baseline=baseline,
            deleted=True,
        )
        EmissionReductionInitiativeFactory(
            name=data["name"],
            emission_management_plan__baseline__asset__tenant=asset.tenant,
            deleted=False,
        )
        EmissionReductionInitiativeFactory(
            name=data["name"],
            deleted=False,
        )
        emission_reduction_initiative = update_emission_reduction_initiative(
            user=user,
            emission_reduction_initiative=emission_reduction_initiative,
            inputs=inputs_data,
            transit=transit,
            **data,
        )

        for field, value in data.items():
            assert getattr(emission_reduction_initiative, field) == value

        emission_reduction_initiative_inputs = (
            EmissionReductionInitiativeInput.objects.inputs()
            .filter(emission_reduction_initiative=emission_reduction_initiative)
            .order_by('pk')
        )

        for emission_reduction_initiative_input, emission_reduction_initiative_input_data in zip(
            emission_reduction_initiative_inputs,
            inputs_data,
        ):
            for field, value in emission_reduction_initiative_input_data.items():
                assert getattr(emission_reduction_initiative_input, field) == value

        emission_reduction_initiative_transit_input.refresh_from_db()
        assert emission_reduction_initiative_transit_input.value == transit

    def test_should_raise_for_non_unique_name_in_relation_to_asset(self):
        asset = AssetFactory()
        user = UserFactory()
        first_emission_reduction_initiative = EmissionReductionInitiativeFactory(
            emission_management_plan__baseline__asset=asset, deleted=False
        )
        second_emission_reduction_initiative = EmissionReductionInitiativeFactory(
            emission_management_plan__baseline__asset=asset, deleted=False
        )

        with pytest.raises(ValidationError) as ex:
            update_emission_reduction_initiative(
                user=user,
                emission_reduction_initiative=first_emission_reduction_initiative,
                name=second_emission_reduction_initiative.name,
                description='Test emission reduction initiative description',
                type=EmissionReductionInitiativeType.PRODUCTIVITY,
                vendor='Test emission reduction initiative vendor',
                inputs=[],
                deployment_date=datetime.date(2022, 1, 14),
                transit=0,
            )

        assert ex.value.message_dict == {'name': ['Energy reduction initiative name is already used.']}

    def test_should_not_raise_when_updating_with_the_same_name(
        self,
        emission_reduction_initiative: EmissionReductionInitiative,
        emission_reduction_initiative_transit_input: EmissionReductionInitiativeInput,
    ):
        user = UserFactory()

        update_emission_reduction_initiative(
            user=user,
            emission_reduction_initiative=emission_reduction_initiative,
            name=emission_reduction_initiative.name,
            description='Test emission reduction initiative description',
            type=EmissionReductionInitiativeType.PRODUCTIVITY,
            vendor='Test emission reduction initiative vendor',
            inputs=[],
            deployment_date=datetime.date(2022, 1, 14),
            transit=0,
        )


@pytest.mark.django_db
class TestCreateEmissionManagementPlan:
    @pytest.fixture
    def data(self):
        return {
            'name': 'Test Create Emission Management Plan',
            'description': 'Test Create Emission Management Plan Description',
            'version': '1.0',
            'draft': True,
        }

    def test_create_emission_management_plan(self, data: dict):
        baseline = BaselineFactory(draft=False)
        user = UserFactory()

        emission_management_plan = create_emission_management_plan(user=user, baseline=baseline, **data)

        for field, value in data.items():
            assert getattr(emission_management_plan, field) == value

        assert emission_management_plan.baseline == baseline
        assert emission_management_plan.active is False

    def test_should_raise_for_draft_baseline(self, data: dict):
        user = UserFactory()
        baseline = BaselineFactory(draft=True)

        with pytest.raises(ValidationError) as ex:
            create_emission_management_plan(user=user, baseline=baseline, **data)

        assert ex.value.message == 'Baseline is still a draft.'

    def test_emission_management_plan_name_is_already_used(self, data: dict):
        asset = AssetFactory()
        baseline = BaselineFactory(draft=False, asset=asset)
        user = UserFactory()
        EmissionManagementPlanFactory(name=data["name"], baseline__asset=asset)

        with pytest.raises(ValidationError) as ex:
            create_emission_management_plan(user=user, baseline=baseline, **data)
        assert ex.value.message_dict == {'name': ['EMP name is already used.']}

    def test_emission_management_plan_name_is_unique_per_asset(self, data: dict):
        asset = AssetFactory()
        baseline = BaselineFactory(draft=False, asset=asset)
        user = UserFactory()
        EmissionManagementPlanFactory.create_batch(2, name=data["name"], deleted=True, baseline__asset=asset)
        EmissionManagementPlanFactory(name=data["name"])

        create_emission_management_plan(user=user, baseline=baseline, **data)


@pytest.mark.django_db
class TestUpdateEmissionManagementPlan:
    @pytest.fixture
    def data(self) -> dict:
        return {
            'name': 'Test Update Emission Management Plan',
            'description': 'Test Update Emission Management Plan Description',
            'version': '1.0',
            'draft': True,
        }

    @pytest.mark.parametrize('old_name,new_name', (('Old name', 'Old name'), ('Old name', 'New name')))
    def test_should_update_emission_management_plan(self, old_name: str, new_name: str, data: dict):
        user = UserFactory()
        emission_management_plan = EmissionManagementPlanFactory(name=old_name)
        EmissionReductionInitiativeFactory(emission_management_plan=emission_management_plan)
        WellPlannerFactory(emission_management_plan=emission_management_plan)

        data = {**data, 'name': new_name, 'draft': False}
        update_emission_management_plan(emission_management_plan=emission_management_plan, user=user, **data)

        emission_management_plan.refresh_from_db()

        for field, value in data.items():
            assert getattr(emission_management_plan, field) == value

    def test_should_make_emission_management_plan_inactive(self, data: dict):
        user = UserFactory()
        emission_management_plan = EmissionManagementPlanFactory(active=True, draft=False)

        update_emission_management_plan(emission_management_plan=emission_management_plan, user=user, **data)

        emission_management_plan.refresh_from_db()

        assert emission_management_plan.draft is True
        assert emission_management_plan.active is False

    def test_emission_management_plan_name_is_already_used(self, data: dict):
        user = UserFactory()
        asset = AssetFactory()
        emission_management_plan = EmissionManagementPlanFactory(baseline__asset=asset)
        EmissionManagementPlanFactory(name=data["name"], baseline__asset=asset)

        with pytest.raises(ValidationError) as ex:
            update_emission_management_plan(emission_management_plan=emission_management_plan, user=user, **data)
        assert ex.value.message_dict == {'name': ['EMP name is already used.']}

    def test_emission_management_plan_name_is_unique_per_asset(self, data: dict):
        user = UserFactory()
        asset = AssetFactory()
        emission_management_plan = EmissionManagementPlanFactory(baseline__asset=asset)
        EmissionManagementPlanFactory.create_batch(2, name=data["name"], deleted=True, baseline__asset=asset)
        EmissionManagementPlanFactory(name=data["name"])

        update_emission_management_plan(emission_management_plan=emission_management_plan, user=user, **data)


@pytest.mark.django_db
class TestDeleteEmissionManagementPlan:
    @pytest.fixture
    def asset(self) -> Asset:
        asset = AssetFactory()
        return asset

    @pytest.fixture
    def emission_management_plan(self, asset) -> EmissionManagementPlan:
        emission_management_plan = EmissionManagementPlanFactory(baseline__asset=asset, active=True, deleted=False)
        WellPlannerFactory(emission_management_plan=emission_management_plan, deleted=True)
        WellPlannerFactory()
        return emission_management_plan

    @pytest.fixture
    def emission_reduction_initiative(
        self, emission_management_plan: EmissionManagementPlan
    ) -> EmissionReductionInitiative:
        emission_reduction_initiative = EmissionReductionInitiativeFactory(
            emission_management_plan=emission_management_plan, deleted=False
        )
        return emission_reduction_initiative

    def test_should_delete_emission_management_plan(
        self,
        emission_management_plan: EmissionManagementPlan,
        emission_reduction_initiative: EmissionReductionInitiative,
    ):
        user = UserFactory()
        another_emission_reduction_initiative = EmissionReductionInitiativeFactory(deleted=False)

        deleted_emission_management_plan = delete_emission_management_plan(
            emission_management_plan=emission_management_plan, user=user
        )

        assert deleted_emission_management_plan.active is False
        assert deleted_emission_management_plan.deleted is True

        emission_reduction_initiative.refresh_from_db()
        assert emission_reduction_initiative.deleted is True

        another_emission_reduction_initiative.refresh_from_db()
        assert another_emission_reduction_initiative.deleted is False

    def test_should_raise_for_emissions_management_plan_used_in_well_planner(
        self, emission_management_plan: EmissionManagementPlan
    ):
        user = UserFactory()
        well_plan = WellPlannerFactory(emission_management_plan=emission_management_plan)

        with pytest.raises(ValidationError) as ex:
            delete_emission_management_plan(emission_management_plan=emission_management_plan, user=user)

        assert ex.value.message == (
            "Energy management plan cannot be deleted right now. "
            f'Energy management plan is used by well plan "{well_plan.name}".'
        )


@pytest.mark.django_db
class TestActivateEmissionManagementPlan:
    def test_should_activate_emission_management_plan(self):
        user = UserFactory()
        baseline = BaselineFactory()
        previous_emission_management_plan = EmissionManagementPlanFactory(baseline=baseline, active=True)
        new_emission_management_plan = EmissionManagementPlanFactory(baseline=baseline, active=False, draft=False)
        unrelated_emission_management_plan = EmissionManagementPlanFactory(active=True)

        activated_emission_management_plan = activate_emission_management_plan(
            emission_management_plan=new_emission_management_plan, user=user
        )

        assert activated_emission_management_plan.pk == new_emission_management_plan.pk
        assert activated_emission_management_plan.active is True

        previous_emission_management_plan.refresh_from_db()
        assert previous_emission_management_plan.active is False

        unrelated_emission_management_plan.refresh_from_db()
        assert unrelated_emission_management_plan.active is True

    def test_should_raise_for_draft_emission_management_plan(self):
        user = UserFactory()
        emission_management_plan = EmissionManagementPlanFactory(draft=True)

        with pytest.raises(ValidationError) as ex:
            activate_emission_management_plan(emission_management_plan=emission_management_plan, user=user)

        assert ex.value.message == 'Energy management plan is still a draft.'


@pytest.mark.django_db
class TestDuplicateEmissionManagementPlan:
    def test_should_duplicate_emission_management_plan(self):
        user = UserFactory()
        emission_management_plan = EmissionManagementPlanFactory()
        (
            emission_reduction_initiative_1,
            emission_reduction_initiative_2,
        ) = EmissionReductionInitiativeFactory.create_batch(2, emission_management_plan=emission_management_plan)
        EmissionReductionInitiativeInputFactory.create_batch(
            2, emission_reduction_initiative=emission_reduction_initiative_1
        )
        EmissionReductionInitiativeInputFactory.create_batch(
            2, emission_reduction_initiative=emission_reduction_initiative_2
        )
        EmissionReductionInitiativeFactory(emission_management_plan=emission_management_plan, deleted=True)

        EmissionReductionInitiativeInputFactory()
        EmissionReductionInitiativeInputFactory(
            emission_reduction_initiative__emission_management_plan__baseline=emission_management_plan.baseline
        )

        duplicated_emission_management_plan = duplicate_emission_management_plan(
            user=user, emission_management_plan=emission_management_plan
        )

        assert duplicated_emission_management_plan.name == f'{emission_management_plan.name} - Copy'
        assert duplicated_emission_management_plan.description == emission_management_plan.description
        assert duplicated_emission_management_plan.baseline == emission_management_plan.baseline
        assert duplicated_emission_management_plan.version == emission_management_plan.version
        assert duplicated_emission_management_plan.draft is True
        assert duplicated_emission_management_plan.active is False

        assert (
            EmissionReductionInitiative.objects.filter(
                emission_management_plan=duplicated_emission_management_plan
            ).count()
            == 2
        )
        assert (
            EmissionReductionInitiativeInput.objects.filter(
                emission_reduction_initiative__emission_management_plan=duplicated_emission_management_plan,
            ).count()
            == 4
        )

    @pytest.mark.freeze_time('2022-05-11')
    def test_emission_management_plan_name_must_be_unique(self):
        user = UserFactory()
        emission_management_plan = EmissionManagementPlanFactory(name='Old name')

        first_copy = duplicate_emission_management_plan(user=user, emission_management_plan=emission_management_plan)

        assert first_copy.name == 'Old name - Copy'

        second_copy = duplicate_emission_management_plan(user=user, emission_management_plan=emission_management_plan)

        assert second_copy.name == 'Old name - Copy - 11.05.2022 00:00:00'

        with pytest.raises(ValidationError) as ex:
            duplicate_emission_management_plan(user=user, emission_management_plan=emission_management_plan)

        assert ex.value.messages == ["Unable to duplicate the energy management plan."]

    @pytest.mark.freeze_time('2022-05-11')
    def test_emission_reduction_initiative_name_must_be_unique(self):
        user = UserFactory()
        emission_reduction_initiative = EmissionReductionInitiativeFactory(name='Old name')

        first_copy = duplicate_emission_management_plan(
            user=user, emission_management_plan=emission_reduction_initiative.emission_management_plan
        )
        first_emission_reduction_initiative_copy = EmissionReductionInitiative.objects.get(
            emission_management_plan=first_copy
        )

        assert first_emission_reduction_initiative_copy.name == 'Old name - Copy'

        second_copy = duplicate_emission_management_plan(
            user=user, emission_management_plan=emission_reduction_initiative.emission_management_plan
        )
        second_emission_reduction_initiative_copy = EmissionReductionInitiative.objects.get(
            emission_management_plan=second_copy
        )

        assert second_emission_reduction_initiative_copy.name == 'Old name - Copy - 11.05.2022 00:00:00'

        emission_reduction_initiative.emission_management_plan.name = 'New name'
        emission_reduction_initiative.emission_management_plan.save()

        with pytest.raises(ValidationError) as ex:
            duplicate_emission_management_plan(
                user=user, emission_management_plan=emission_reduction_initiative.emission_management_plan
            )

        assert ex.value.messages == ["Unable to duplicate the energy reduction initiative."]


@pytest.mark.django_db
@pytest.mark.parametrize('HelicopterUseFactory', (PlannedHelicopterUseFactory, CompleteHelicopterUseFactory))
class TestDeleteHelicopterType:
    def test_should_delete_helicopter_type(
        self, HelicopterUseFactory: type[PlannedHelicopterUseFactory | CompleteHelicopterUseFactory]
    ):
        user = UserFactory()
        helicopter_type = HelicopterTypeFactory()
        HelicopterUseFactory(helicopter_type=helicopter_type, well_planner__deleted=True)
        HelicopterUseFactory()

        assert helicopter_type.deleted is False

        deleted_helicopter_type = delete_helicopter_type(user=user, helicopter_type=helicopter_type)

        assert deleted_helicopter_type.deleted is True

    def test_should_raise_for_helicopter_type_connected_to_well_plan(
        self, HelicopterUseFactory: type[PlannedHelicopterUseFactory | CompleteHelicopterUseFactory]
    ):
        helicopter_type = HelicopterTypeFactory()
        helicopter_use = HelicopterUseFactory(helicopter_type=helicopter_type)
        user = UserFactory()

        with pytest.raises(ValidationError) as ex:
            delete_helicopter_type(helicopter_type=helicopter_type, user=user)
        assert (
            ex.value.message
            == f"Helicopter type cannot be deleted right now. Helicopter type is used by well plan \"{helicopter_use.well_planner.name}\"."
        )


@pytest.mark.django_db
class TestCreateHelicopterType:
    def test_should_create_helicopter_type(self, helicopter_type_data: dict):
        tenant = TenantFactory()
        user = UserFactory()

        helicopter_type = create_helicopter_type(user=user, tenant=tenant, **helicopter_type_data)

        for field, value in helicopter_type_data.items():
            assert getattr(helicopter_type, field) == value

        assert helicopter_type.tenant == tenant
        assert helicopter_type.deleted is False


@pytest.mark.django_db
class TestUpdateHelicopterType:
    def test_should_update_helicopter_type(self, helicopter_type_data: dict):
        user = UserFactory()
        helicopter_type = HelicopterTypeFactory()

        updated_helicopter_type = update_helicopter_type(
            helicopter_type=helicopter_type, user=user, **helicopter_type_data
        )

        assert updated_helicopter_type.pk == helicopter_type.pk

        for field, value in helicopter_type_data.items():
            assert getattr(helicopter_type, field) == value


@pytest.mark.django_db
class TestDeleteEmissionReductionInitiative:
    def test_should_delete_emission_reduction_initiative(self):
        user = UserFactory()
        emission_reduction_initiative = EmissionReductionInitiativeFactory(deleted=False)
        WellPlannerFactory(
            emission_management_plan=emission_reduction_initiative.emission_management_plan, deleted=True
        )
        WellPlannerFactory()

        deleted_emission_reduction_initiative = delete_emission_reduction_initiative(
            emission_reduction_initiative=emission_reduction_initiative, user=user
        )

        assert deleted_emission_reduction_initiative.deleted is True

    def test_should_raise_for_used_emission_management_plan(self):
        user = UserFactory()
        emission_reduction_initiative = EmissionReductionInitiativeFactory(emission_management_plan__active=True)
        well_plan = WellPlannerFactory(emission_management_plan=emission_reduction_initiative.emission_management_plan)

        with pytest.raises(ValidationError) as ex:
            delete_emission_reduction_initiative(emission_reduction_initiative=emission_reduction_initiative, user=user)

        assert ex.value.message == (
            "Energy reduction initiative cannot be deleted right now. "
            f'Energy reduction initiative is used by well plan "{well_plan.name}".'
        )


@pytest.mark.django_db
def test_baseline_phases():
    asset = AssetFactory()
    baseline = BaselineFactory(asset=asset)
    first_phase, second_phase, _ = CustomPhaseFactory.create_batch(3, asset=asset)
    CustomPhaseFactory()
    mode = CustomModeFactory(asset=asset)
    BaselineInputFactory(baseline=baseline, phase=second_phase, mode=mode, season=AssetSeason.SUMMER, order=1)
    BaselineInputFactory(baseline=baseline, phase=first_phase, mode=mode, season=AssetSeason.SUMMER, order=2)
    BaselineInputFactory(baseline=baseline, phase=second_phase, mode=mode, season=AssetSeason.WINTER, order=3)
    BaselineInputFactory(baseline=baseline, phase=first_phase, mode=mode, season=AssetSeason.WINTER, order=4)

    assert list(baseline_phases(baseline)) == [second_phase, first_phase]


@pytest.mark.django_db
def test_baseline_modes():
    asset = AssetFactory()
    baseline = BaselineFactory(asset=asset)
    first_mode, second_mode, _ = CustomModeFactory.create_batch(3, asset=asset)
    CustomModeFactory()
    phase = CustomPhaseFactory(asset=asset)
    BaselineInputFactory(baseline=baseline, mode=second_mode, phase=phase, season=AssetSeason.SUMMER, order=1)
    BaselineInputFactory(baseline=baseline, mode=first_mode, phase=phase, season=AssetSeason.SUMMER, order=2)
    BaselineInputFactory(baseline=baseline, mode=second_mode, phase=phase, season=AssetSeason.WINTER, order=3)
    BaselineInputFactory(baseline=baseline, mode=first_mode, phase=phase, season=AssetSeason.WINTER, order=4)

    assert list(baseline_modes(baseline)) == [second_mode, first_mode]


@pytest.mark.django_db
@pytest.mark.parametrize(
    'WellStepMaterialFactory',
    (
        (
            WellPlannedStepMaterialFactory,
            WellCompleteStepMaterialFactory,
        )
    ),
)
class TestDeleteMaterialType:
    def test_should_delete_material_type(
        self,
        WellStepMaterialFactory: type[WellPlannedStepMaterialFactory | WellCompleteStepMaterialFactory],
    ):
        user = UserFactory()
        material = WellStepMaterialFactory(step__well_planner__deleted=True)

        deleted_material_type = delete_material_type(material_type=material.material_type, user=user)

        assert deleted_material_type.deleted is True

    def test_should_raise_for_material_type_connected_to_well_plan(
        self,
        WellStepMaterialFactory: type[WellPlannedStepMaterialFactory | WellCompleteStepMaterialFactory],
    ):
        user = UserFactory()
        material = WellStepMaterialFactory()

        with pytest.raises(ValidationError) as ex:
            delete_material_type(material_type=material.material_type, user=user)

        assert (
            ex.value.message
            == f"Material type cannot be deleted right now. Material type is used by well plan \"{material.step.well_planner.name}\"."
        )


@pytest.mark.django_db
class TestCreateMaterialType:
    def test_should_create_material_type(self):
        tenant = TenantFactory()
        user = UserFactory()

        data = {
            "category": MaterialCategory.CEMENT,
            "type": "Test material type",
            "unit": "kg",
            "co2": 100,
        }

        material_type = create_material_type(user=user, tenant=tenant, **data)

        for field, value in data.items():
            assert getattr(material_type, field) == value

        assert material_type.tenant == tenant


@pytest.mark.django_db
class TestUpdateMaterialType:
    def test_should_update_material_type(self):
        user = UserFactory()
        material_type = MaterialTypeFactory()

        data = {
            "type": "Test material type",
            "unit": "kg",
            "co2": 100,
        }

        updated_material_type = update_material_type(material_type=material_type, user=user, **data)

        assert updated_material_type.pk == material_type.pk

        for field, value in data.items():
            assert getattr(material_type, field) == value
