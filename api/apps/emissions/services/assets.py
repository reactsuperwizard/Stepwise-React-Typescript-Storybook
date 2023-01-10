import datetime
import itertools
import logging
from typing import Callable, TypedDict, cast

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import OuterRef, Q, Subquery
from django.utils import timezone

from apps.emissions.consts import INITIAL_CONCEPT_MODES, INITIAL_CONCEPT_PHASES
from apps.emissions.models import (
    Asset,
    AssetSeason,
    AssetType,
    Baseline,
    BaselineInput,
    CompleteHelicopterUse,
    CompleteVesselUse,
    ConceptMode,
    ConceptPhase,
    CustomMode,
    CustomPhase,
    EmissionManagementPlan,
    EmissionReductionInitiative,
    EmissionReductionInitiativeInput,
    EmissionReductionInitiativeType,
    ExternalEnergySupply,
    HelicopterType,
    MaterialCategory,
    MaterialType,
    PlannedHelicopterUse,
    PlannedVesselUse,
    VesselType,
)
from apps.kims.models import Vessel
from apps.tenants.models import Tenant
from apps.wells.models import WellPlanner

logger = logging.getLogger(__name__)


class BaselineInputData(TypedDict):
    phase: CustomPhase
    mode: CustomMode
    value: float


class BaselineSeasonData(TypedDict):
    inputs: list[BaselineInputData]
    transit: float


class EmissionReductionInitiativeInputData(TypedDict):
    phase: CustomPhase
    mode: CustomMode
    value: float


class ExternalEnergySupplyInputData(TypedDict):
    type: str
    capacity: float
    co2: float
    nox: float
    generator_efficiency_factor: float


def create_asset_phases(tenant: Tenant, asset: Asset) -> None:
    CustomPhase.objects.bulk_create(
        CustomPhase(
            asset=asset,
            name=phase.name,
            description=phase.description,
            phase=phase,
        )
        for phase in tenant.conceptphase_set.all()
    )


def create_asset_modes(tenant: Tenant, asset: Asset) -> None:
    CustomMode.objects.bulk_create(
        CustomMode(
            asset=asset,
            name=mode.name,
            description=mode.description,
            mode=mode,
        )
        for mode in tenant.conceptmode_set.filter(asset_types__contains=[asset.type])
    )


def get_complete_assets(tenant: Tenant) -> models.QuerySet["Asset"]:
    active_baselines = Baseline.objects.live().filter(active=True, asset=OuterRef('pk'))
    active_emission_management_plans = EmissionManagementPlan.objects.live().filter(
        active=True, baseline__active=True, baseline__asset=OuterRef('pk')
    )
    assets = (
        Asset.objects.live()
        .filter(tenant=tenant, draft=False)
        .annotate(
            active_baseline=Subquery(active_baselines.values('name')[:1]),
            active_emission_management_plan=Subquery(active_emission_management_plans.values('name')[:1]),
        )
        .order_by('created_at')
    )
    return cast(models.QuerySet["Asset"], assets)


@transaction.atomic
def create_asset(
    *,
    tenant: Tenant,
    user: User,
    name: str,
    type: AssetType,
    design_description: str,
    green_house_gas_class_notation: str,
    external_energy_supply: ExternalEnergySupplyInputData,
) -> Asset:
    logger.info(f"User(pk={user.pk}) is creating new Asset.")

    if Asset.objects.live().filter(name=name).exists():
        raise ValidationError({"name": "Asset name is already used."})

    asset = Asset.objects.create(
        tenant=tenant,
        name=name,
        vessel=Vessel.objects.filter(name=name).first(),
        type=type,
        design_description=design_description,
        green_house_gas_class_notation=green_house_gas_class_notation,
        draft=True,
    )
    ExternalEnergySupply.objects.create(
        asset=asset,
        type=external_energy_supply["type"],
        capacity=external_energy_supply["capacity"],
        co2=external_energy_supply["co2"],
        nox=external_energy_supply["nox"],
        generator_efficiency_factor=external_energy_supply["generator_efficiency_factor"],
    )
    create_asset_phases(tenant, asset)
    create_asset_modes(tenant, asset)

    logger.info(f'Asset(pk={asset.pk}) has been created.')
    return asset


@transaction.atomic
def update_asset(
    *,
    asset: Asset,
    user: User,
    draft: bool,
    name: str,
    type: AssetType,
    design_description: str,
    green_house_gas_class_notation: str,
    external_energy_supply: ExternalEnergySupplyInputData,
) -> Asset:
    logger.info(f"User(pk={user.pk}) is updating Asset(pk={asset.pk}).")

    if Asset.objects.live().filter(name=name).exclude(pk=asset.pk).exists():
        raise ValidationError({"name": "Asset name is already used."})

    if not draft and not Baseline.objects.live().filter(asset=asset, active=True).exists():
        raise ValidationError({"draft": "Status cannot be changed without having an active baseline."})

    asset.name = name
    asset.vessel = Vessel.objects.filter(name=asset.name).first()
    asset.type = type
    asset.design_description = design_description
    asset.green_house_gas_class_notation = green_house_gas_class_notation
    asset.draft = draft
    asset.save()

    asset_external_energy_supply = asset.external_energy_supply
    asset_external_energy_supply.type = external_energy_supply["type"]
    asset_external_energy_supply.capacity = external_energy_supply["capacity"]
    asset_external_energy_supply.co2 = external_energy_supply["co2"]
    asset_external_energy_supply.nox = external_energy_supply["nox"]
    asset_external_energy_supply.generator_efficiency_factor = external_energy_supply["generator_efficiency_factor"]
    asset_external_energy_supply.save()

    logger.info(f'Asset(pk={asset.pk}) has been created.')

    return asset


def duplicate_asset_name(old_name: str, name_max_length: int) -> str | None:
    suffixes = [' - Copy', f' - Copy - {timezone.now().strftime("%d.%m.%Y %H:%M:%S")}']
    for suffix in suffixes:
        new_name = f'{old_name[:name_max_length - len(suffix)]}{suffix}'
        if not Asset.objects.live().filter(name=new_name).exists():
            return new_name
    return None


@transaction.atomic
def duplicate_asset(*, asset: Asset, user: User) -> Asset:
    logger.info(f"User(pk={user.pk}) is duplicating Asset(pk={asset.pk}).")
    name_max_length = Asset._meta.get_field('name').max_length
    asset_name = duplicate_asset_name(asset.name, name_max_length)
    if not asset_name:
        raise ValidationError("Unable to duplicate the asset.")
    asset_copy = Asset.objects.create(
        tenant=asset.tenant,
        name=asset_name,
        vessel=Vessel.objects.filter(name=asset_name).first(),
        type=asset.type,
        design_description=asset.design_description,
        green_house_gas_class_notation=asset.green_house_gas_class_notation,
        draft=True,
    )
    logger.info('Asset has been duplicated.')

    external_energy_supply = asset.external_energy_supply
    ExternalEnergySupply.objects.create(
        asset=asset_copy,
        type=external_energy_supply.type,
        capacity=external_energy_supply.capacity,
        co2=external_energy_supply.co2,
        nox=external_energy_supply.nox,
        generator_efficiency_factor=external_energy_supply.generator_efficiency_factor,
    )

    logger.info('ExternalEnergySupply has been duplicated.')

    create_asset_phases(asset.tenant, asset_copy)
    create_asset_modes(asset.tenant, asset_copy)

    return asset_copy


def delete_asset(*, asset: Asset, user: User) -> Asset:
    logger.info(f"User(pk={user.pk}) is deleting Asset(pk={asset.pk}).")

    if well_plan := WellPlanner.objects.live().filter(asset=asset).first():
        raise ValidationError(f"Asset cannot be deleted right now. Asset is used by well plan \"{well_plan.name}\".")

    asset.deleted = True
    asset.vessel = None
    asset.save()

    logger.info('Asset has been deleted.')
    return asset


@transaction.atomic
def activate_baseline(*, baseline: Baseline, user: User) -> Baseline:
    logger.info(f"User(pk={user.pk}) is activating Baseline(pk={baseline.pk}).")

    if baseline.draft:
        raise ValidationError("Only complete baselines can be activated.")

    Baseline.objects.filter(asset=baseline.asset, active=True).update(active=False)
    baseline.active = True
    baseline.save()

    logger.info('Baseline has been activated.')
    return baseline


@transaction.atomic
def delete_baseline(*, baseline: Baseline, user: User) -> Baseline:
    logger.info(f"User(pk={user.pk}) is deleting Baseline(pk={baseline.pk}).")

    if well_plan := WellPlanner.objects.live().filter(baseline=baseline).first():
        raise ValidationError(
            f"Baseline cannot be deleted right now. Baseline is used by well plan \"{well_plan.name}\"."
        )

    if baseline.active:
        asset = baseline.asset
        asset.draft = True
        asset.save()

    baseline.deleted = True
    baseline.active = False
    baseline.save()

    logger.info('Baseline has been deleted.')
    return baseline


def duplicate_baseline_name(*, old_name: str, name_max_length: int, asset: Asset) -> str | None:
    suffixes = [' - Copy', f' - Copy - {timezone.now().strftime("%d.%m.%Y %H:%M:%S")}']
    for suffix in suffixes:
        new_name = f'{old_name[:name_max_length - len(suffix)]}{suffix}'
        if not Baseline.objects.live().filter(name=new_name, asset=asset).exists():
            return new_name
    return None


@transaction.atomic
def duplicate_baseline(*, baseline: Baseline, user: User) -> Baseline:
    logger.info(f"User(pk={user.pk}) is duplicating Baseline(pk={baseline.pk}).")

    name_max_length = Baseline._meta.get_field('name').max_length
    baseline_name = duplicate_baseline_name(
        old_name=baseline.name, name_max_length=name_max_length, asset=baseline.asset
    )
    if not baseline_name:
        raise ValidationError("Unable to duplicate the baseline.")

    baseline_copy = Baseline.objects.create(
        asset=baseline.asset,
        name=baseline_name,
        description=baseline.description,
        boilers_fuel_consumption_summer=baseline.boilers_fuel_consumption_summer,
        boilers_fuel_consumption_winter=baseline.boilers_fuel_consumption_winter,
        active=False,
        draft=True,
    )

    baseline_inputs = BaselineInput.objects.filter(baseline=baseline).select_related('phase', 'mode')
    BaselineInput.objects.bulk_create(
        BaselineInput(
            baseline=baseline_copy,
            season=baseline_input.season,
            phase=baseline_input.phase,
            mode=baseline_input.mode,
            value=baseline_input.value,
            order=baseline_input.order,
        )
        for baseline_input in baseline_inputs
    )

    logger.info(f'Baseline(pk={baseline_copy.pk}) has been created.')
    return baseline_copy


def create_initial_concept_phases(tenant: Tenant) -> None:
    logger.info(f'Creating initial concept phases for Tenant(pk={tenant.pk}).')

    ConceptPhase.objects.bulk_create(
        ConceptPhase(
            tenant=tenant,
            name=name,
            description=description,
            transit=transit,
        )
        for name, description, transit in INITIAL_CONCEPT_PHASES
    )

    logger.info('Initial concept phases have been created.')


def create_initial_concept_modes(tenant: Tenant) -> None:
    logger.info(f'Creating concept modes for Tenant(pk={tenant.pk}).')

    ConceptMode.objects.bulk_create(
        ConceptMode(tenant=tenant, name=name, description=description, asset_types=asset_types, transit=transit)
        for name, description, asset_types, transit in INITIAL_CONCEPT_MODES
    )

    logger.info('Initial concept modes have been created.')


def create_custom_phase(
    *,
    user: User,
    asset: Asset,
    name: str,
    description: str,
) -> CustomPhase:
    logger.info(f'User(pk={user.pk}) is creating custom phase for Asset(pk={asset.pk}).')

    if CustomPhase.objects.filter(asset=asset, name=name).exists():
        raise ValidationError('Phase with this name already exists.')

    custom_phase = CustomPhase.objects.create(
        asset=asset,
        name=name,
        description=description,
        phase=None,
    )

    logger.info(f'CustomPhase(pk={custom_phase.pk}) has been created.')
    return custom_phase


def update_custom_phase(
    *,
    user: User,
    custom_phase: CustomPhase,
    name: str,
    description: str,
) -> CustomPhase:
    logger.info(f'User(pk={user.pk}) is updating CustomPhase(pk={custom_phase.pk}).')

    if custom_phase.phase_id is not None:
        raise ValidationError('Only custom phases can be updated.')

    if CustomPhase.objects.filter(asset=custom_phase.asset, name=name).exclude(pk=custom_phase.pk).exists():
        raise ValidationError('Phase with this name already exists.')

    custom_phase.name = name
    custom_phase.description = description
    custom_phase.save()

    logger.info(f'CustomPhase(pk={custom_phase.pk}) has been updated.')
    return custom_phase


def create_custom_mode(
    *,
    user: User,
    asset: Asset,
    name: str,
    description: str,
) -> CustomMode:
    logger.info(f'User(pk={user.pk}) is creating custom mode for Asset(pk={asset.pk}).')

    if CustomMode.objects.filter(asset=asset, name=name).exists():
        raise ValidationError('Mode with this name already exists.')

    custom_mode = CustomMode.objects.create(
        asset=asset,
        name=name,
        description=description,
        mode=None,
    )

    logger.info(f'CustomMode(pk={custom_mode.pk}) has been created.')
    return custom_mode


def update_custom_mode(
    *,
    user: User,
    custom_mode: CustomMode,
    name: str,
    description: str,
) -> CustomMode:
    logger.info(f'User(pk={user.pk}) is updating CustomMode(pk={custom_mode.pk}).')

    if custom_mode.mode_id is not None:
        raise ValidationError('Only custom modes can be updated.')

    if CustomMode.objects.filter(asset=custom_mode.asset, name=name).exclude(pk=custom_mode.pk).exists():
        raise ValidationError('Mode with this name already exists.')

    custom_mode.name = name
    custom_mode.description = description
    custom_mode.save()

    logger.info(f'CustomMode(pk={custom_mode.pk}) has been updated.')
    return custom_mode


def validate_baseline_data(*, asset: Asset, winter: BaselineSeasonData, summer: BaselineSeasonData) -> None:
    logger.info('Validating baseline data.')

    required_phases = set(CustomPhase.objects.filter(asset=asset, phase__transit=False).values_list('pk', flat=True))
    phases = [input_data['phase'] for input_data in itertools.chain(winter['inputs'], summer['inputs'])]

    for phase in phases:
        if not CustomPhase.objects.filter(asset=asset, pk=phase.pk).exclude(phase__transit=True).exists():
            logger.info(
                f"Baseline inputs invalid. CustomPhase(pk={phase.pk}, transit={phase.transit}) is not a valid choice."
            )
            raise ValidationError('Chosen phase is not a valid choice.')

    input_phases = {phase.pk for phase in phases}
    if not input_phases.issuperset(required_phases):
        raise ValidationError('Provide all required phases.')

    modes = [input_data['mode'] for input_data in itertools.chain(winter['inputs'], summer['inputs'])]

    for mode in modes:
        if not CustomMode.objects.filter(asset=asset, pk=mode.pk).exclude(mode__transit=True).exists():
            logger.info(
                f"Baseline inputs invalid. CustomMode(pk={mode.pk}, transit={mode.transit}) is not a valid choice."
            )
            raise ValidationError('Chosen mode is not a valid choice.')

    if not modes:
        raise ValidationError('Add at least one mode.')

    required_combinations = {
        (phase.pk, mode.pk, season) for phase, mode, season in itertools.product(phases, modes, AssetSeason.values)
    }
    input_combinations = {
        (input_data['phase'].pk, input_data['mode'].pk, season)
        for season, input_data in itertools.chain(
            map(lambda input_data: (AssetSeason.WINTER, input_data), winter['inputs']),
            map(lambda input_data: (AssetSeason.SUMMER, input_data), summer['inputs']),
        )
    }

    if required_combinations != input_combinations:
        logger.info(
            'Baseline inputs invalid. Not all required combinations are present. Difference is %s.',
            required_combinations.difference(input_combinations),
        )
        raise ValidationError('All baseline inputs are required.')

    logger.info('Baseline data has been validated.')


def get_transit_phase_and_mode(*, asset_id: int) -> tuple[CustomPhase, CustomMode]:
    transit_phase = CustomPhase.objects.get(asset=asset_id, phase__transit=True)
    transit_mode = CustomMode.objects.get(asset=asset_id, mode__transit=True)

    return transit_phase, transit_mode


@transaction.atomic
def create_baseline(
    *,
    user: User,
    asset: Asset,
    name: str,
    description: str,
    draft: bool,
    boilers_fuel_consumption_summer: float,
    boilers_fuel_consumption_winter: float,
    summer: BaselineSeasonData,
    winter: BaselineSeasonData,
) -> Baseline:
    logger.info(f'User(pk={user.pk}) is creating baseline for Asset(pk={asset.pk}).')

    if Baseline.objects.live().filter(asset=asset, name=name).exists():
        raise ValidationError({"name": "Baseline name is already used."})

    validate_baseline_data(asset=asset, winter=winter, summer=summer)

    baseline = Baseline.objects.create(
        asset=asset,
        name=name,
        description=description,
        boilers_fuel_consumption_summer=boilers_fuel_consumption_summer,
        boilers_fuel_consumption_winter=boilers_fuel_consumption_winter,
        draft=draft,
        active=False,
    )
    transit_phase, transit_mode = get_transit_phase_and_mode(asset_id=asset.pk)

    inputs_by_season = itertools.chain(
        map(lambda input_data: (AssetSeason.WINTER, input_data), winter['inputs']),
        map(lambda input_data: (AssetSeason.SUMMER, input_data), summer['inputs']),
        (
            (AssetSeason.WINTER, BaselineInputData(phase=transit_phase, mode=transit_mode, value=winter['transit'])),
            (AssetSeason.SUMMER, BaselineInputData(phase=transit_phase, mode=transit_mode, value=summer['transit'])),
        ),
    )
    BaselineInput.objects.bulk_create(
        BaselineInput(baseline=baseline, order=order, season=season, **input_data)
        for order, (season, input_data) in enumerate(inputs_by_season)
    )

    logger.info(f'Baseline(pk={baseline.pk}) has been created.')
    return baseline


@transaction.atomic
def update_baseline(
    *,
    user: User,
    baseline: Baseline,
    name: str,
    description: str,
    draft: bool,
    boilers_fuel_consumption_summer: float,
    boilers_fuel_consumption_winter: float,
    summer: BaselineSeasonData,
    winter: BaselineSeasonData,
) -> Baseline:
    logger.info(f'User(pk={user.pk}) is updating Baseline(pk={baseline.pk}).')

    if Baseline.objects.live().filter(name=name, asset=baseline.asset).exclude(pk=baseline.pk).exists():
        raise ValidationError({"name": "Baseline name is already used."})

    validate_baseline_data(asset=baseline.asset, winter=winter, summer=summer)

    baseline.name = name
    baseline.description = description
    baseline.boilers_fuel_consumption_summer = boilers_fuel_consumption_summer
    baseline.boilers_fuel_consumption_winter = boilers_fuel_consumption_winter
    baseline.draft = draft
    if draft and baseline.active:
        baseline.active = False
        asset = baseline.asset
        asset.draft = True
        asset.save()
    baseline.save()

    logger.info('Updating baseline inputs.')

    all_input_phases = map(lambda input_data: input_data['phase'], winter['inputs'])
    all_input_modes = map(lambda input_data: input_data['mode'], winter['inputs'])

    baseline_inputs_to_delete = (
        BaselineInput.objects.inputs()
        .filter(baseline=baseline)
        .exclude(Q(phase__in=all_input_phases) & Q(mode__in=all_input_modes))
    )

    if baseline_inputs_to_delete.exists() and baseline.is_used:
        logger.info(
            f"Unable to update Baseline(pk={baseline.pk}). "
            f"Attempted to remove BaselineInput(pk__in={baseline_inputs_to_delete.values_list('pk', flat=True)}) "
            "in a used baseline."
        )
        raise ValidationError("Inputs can not be removed in a used baseline.")

    for baseline_input_to_delete in baseline_inputs_to_delete:
        logger.info(f"Deleting BaselineInput(pk={baseline_input_to_delete.pk}).")
        baseline_input_to_delete.delete()

    transit_phase, transit_mode = get_transit_phase_and_mode(asset_id=baseline.asset_id)
    inputs_by_season = itertools.chain(
        map(lambda input_data: (AssetSeason.WINTER, input_data), winter['inputs']),
        map(lambda input_data: (AssetSeason.SUMMER, input_data), summer['inputs']),
        (
            (AssetSeason.WINTER, BaselineInputData(phase=transit_phase, mode=transit_mode, value=winter['transit'])),
            (AssetSeason.SUMMER, BaselineInputData(phase=transit_phase, mode=transit_mode, value=summer['transit'])),
        ),
    )

    new_input_phase_mode_combinations: set[tuple[CustomPhase, CustomMode]] = set()

    for index, (season, baseline_input_data) in enumerate(inputs_by_season):
        baseline_input, baseline_input_created = BaselineInput.objects.update_or_create(
            baseline=baseline,
            season=season,
            phase=baseline_input_data['phase'],
            mode=baseline_input_data['mode'],
            defaults={
                'order': index,
                'value': baseline_input_data['value'],
            },
        )

        if baseline_input_created:
            logger.info(f'BaselineInput(pk={baseline_input.pk}) has been created.')
            new_input_phase_mode_combinations.add((baseline_input_data['phase'], baseline_input_data['mode']))
        else:
            logger.info(f'BaselineInput(pk={baseline_input.pk}) has been updated.')

    if new_input_phase_mode_combinations and baseline.is_used:
        logger.info(f"Creating missing EmissionReductionInitiativeInputs for Baseline(pk={baseline.pk}).")
        for emission_reduction_initiative in EmissionReductionInitiative.objects.live().filter(
            emission_management_plan__baseline=baseline,
        ):
            for phase, mode in new_input_phase_mode_combinations:
                emission_reduction_initiative_input = EmissionReductionInitiativeInput.objects.create(
                    emission_reduction_initiative=emission_reduction_initiative,
                    phase=phase,
                    mode=mode,
                    value=0,
                )
                logger.info(
                    f"EmissionReductionInitiativeInput(pk={emission_reduction_initiative_input.pk}) "
                    "has been created."
                )

    logger.info(f'Baseline(pk={baseline.pk}) has been updated.')
    return baseline


def create_vessel_type(
    *,
    tenant: Tenant,
    user: User,
    type: str,
    fuel_type: str,
    fuel_density: float,
    co2_per_fuel: float,
    nox_per_fuel: float,
    co2_tax: float,
    nox_tax: float,
    fuel_cost: float,
    fuel_consumption_summer: float,
    fuel_consumption_winter: float,
) -> VesselType:
    logger.info(f'User(pk={user.pk}) is creating a new VesselType')

    vessel_type = VesselType.objects.create(
        type=type,
        fuel_type=fuel_type,
        fuel_density=fuel_density,
        co2_per_fuel=co2_per_fuel,
        nox_per_fuel=nox_per_fuel,
        co2_tax=co2_tax,
        nox_tax=nox_tax,
        fuel_cost=fuel_cost,
        fuel_consumption_summer=fuel_consumption_summer,
        fuel_consumption_winter=fuel_consumption_winter,
        tenant=tenant,
        deleted=False,
    )
    logger.info(f'VesselType(pk=${vessel_type.pk}) has been created')

    return vessel_type


def update_vessel_type(
    *,
    vessel_type: VesselType,
    user: User,
    type: str,
    fuel_type: str,
    fuel_density: float,
    co2_per_fuel: float,
    nox_per_fuel: float,
    co2_tax: float,
    nox_tax: float,
    fuel_cost: float,
    fuel_consumption_summer: float,
    fuel_consumption_winter: float,
) -> VesselType:
    logger.info(f'User(pk={user.pk}) is updating VesselType(pk={vessel_type.pk})')

    vessel_type.type = type
    vessel_type.fuel_type = fuel_type
    vessel_type.fuel_density = fuel_density
    vessel_type.co2_per_fuel = co2_per_fuel
    vessel_type.nox_per_fuel = nox_per_fuel
    vessel_type.co2_tax = co2_tax
    vessel_type.nox_tax = nox_tax
    vessel_type.fuel_cost = fuel_cost
    vessel_type.fuel_consumption_summer = fuel_consumption_summer
    vessel_type.fuel_consumption_winter = fuel_consumption_winter
    vessel_type.save()

    logger.info('VesselType has been updated')

    return vessel_type


def delete_vessel_type(
    *,
    vessel_type: VesselType,
    user: User,
) -> VesselType:
    logger.info(f'User(pk={user.pk}) is deleting VesselType(pk={vessel_type.pk})')

    if planned_vessel_use := PlannedVesselUse.objects.filter(
        vessel_type=vessel_type, well_planner__deleted=False
    ).first():
        raise ValidationError(
            f"Vessel type cannot be deleted right now. "
            f"Vessel type is used by well plan \"{planned_vessel_use.well_planner.name}\"."
        )
    if complete_vessel_use := CompleteVesselUse.objects.filter(
        vessel_type=vessel_type, well_planner__deleted=False
    ).first():
        raise ValidationError(
            f"Vessel type cannot be deleted right now. "
            f"Vessel type is used by well plan \"{complete_vessel_use.well_planner.name}\"."
        )

    vessel_type.deleted = True
    vessel_type.save()

    logger.info('VesselType has been deleted.')
    return vessel_type


def validate_emission_reduction_initiative_data(
    *,
    emission_management_plan: EmissionManagementPlan,
    inputs: list[EmissionReductionInitiativeInputData],
) -> None:
    logger.info('Validating emission reduction initiative data.')

    baseline_inputs = (
        BaselineInput.objects.inputs()
        .filter(baseline=emission_management_plan.baseline_id)
        .select_related('phase', 'mode')
    )
    phases = {baseline_input.phase for baseline_input in baseline_inputs}
    modes = {baseline_input.mode for baseline_input in baseline_inputs}

    required_combinations = {(phase.pk, mode.pk) for phase, mode in itertools.product(phases, modes)}
    input_combinations = {(input_data['phase'].pk, input_data['mode'].pk) for input_data in inputs}

    if required_combinations != input_combinations:
        logger.info(
            'Emission reduction initiative inputs invalid. Not all required combinations are present. Difference is %s.',
            required_combinations.difference(input_combinations),
        )
        raise ValidationError('All energy reduction initiative inputs are required.')

    logger.info('Emission reduction initiative data has been validated.')


@transaction.atomic
def create_emission_reduction_initiative(
    *,
    user: User,
    emission_management_plan: EmissionManagementPlan,
    name: str,
    description: str,
    type: EmissionReductionInitiativeType,
    vendor: str,
    deployment_date: datetime.date,
    inputs: list[EmissionReductionInitiativeInputData],
    transit: float,
) -> EmissionReductionInitiative:
    logger.info(
        f'User(pk={user.pk}) is creating emission reduction initiative for EmissionManagementPlan(pk={emission_management_plan.pk}).'
    )

    validate_emission_reduction_initiative_data(
        emission_management_plan=emission_management_plan,
        inputs=inputs,
    )

    if (
        EmissionReductionInitiative.objects.live()
        .filter(
            emission_management_plan__baseline__asset=emission_management_plan.baseline.asset,
            name=name,
        )
        .exists()
    ):
        raise ValidationError({'name': 'Energy reduction initiative name is already used.'})

    emission_reduction_initiative = EmissionReductionInitiative.objects.create(
        emission_management_plan=emission_management_plan,
        name=name,
        description=description,
        type=type,
        vendor=vendor,
        deployment_date=deployment_date,
    )

    transit_baseline_input = BaselineInput.objects.transit().get(
        baseline=emission_management_plan.baseline_id, season=AssetSeason.SUMMER
    )

    EmissionReductionInitiativeInput.objects.create(
        emission_reduction_initiative=emission_reduction_initiative,
        phase=transit_baseline_input.phase,
        mode=transit_baseline_input.mode,
        value=transit,
    )
    EmissionReductionInitiativeInput.objects.bulk_create(
        EmissionReductionInitiativeInput(
            emission_reduction_initiative=emission_reduction_initiative, **baseline_input_data
        )
        for baseline_input_data in inputs
    )

    logger.info(f'EmissionReductionInitiative(pk={emission_reduction_initiative.pk}) has been created.')
    return emission_reduction_initiative


@transaction.atomic
def update_emission_reduction_initiative(
    *,
    user: User,
    emission_reduction_initiative: EmissionReductionInitiative,
    name: str,
    description: str,
    type: EmissionReductionInitiativeType,
    vendor: str,
    deployment_date: datetime.date,
    inputs: list[EmissionReductionInitiativeInputData],
    transit: float,
) -> EmissionReductionInitiative:
    logger.info(f'User(pk={user.pk}) is updating EmissionReductionInitiative(pk={emission_reduction_initiative.pk}).')

    validate_emission_reduction_initiative_data(
        emission_management_plan=emission_reduction_initiative.emission_management_plan,
        inputs=inputs,
    )

    if (
        EmissionReductionInitiative.objects.live()
        .exclude(pk=emission_reduction_initiative.pk)
        .filter(
            emission_management_plan__baseline__asset=emission_reduction_initiative.emission_management_plan.baseline.asset,
            name=name,
        )
        .exists()
    ):
        raise ValidationError({'name': 'Energy reduction initiative name is already used.'})

    emission_reduction_initiative.name = name
    emission_reduction_initiative.description = description
    emission_reduction_initiative.type = type
    emission_reduction_initiative.vendor = vendor
    emission_reduction_initiative.deployment_date = deployment_date
    emission_reduction_initiative.save()

    logger.info('Updating emission reduction initiative inputs.')

    transit_emission_reduction_initiative_input = EmissionReductionInitiativeInput.objects.transit().get(
        emission_reduction_initiative=emission_reduction_initiative,
    )

    transit_emission_reduction_initiative_input.value = transit
    transit_emission_reduction_initiative_input.save()
    logger.info(
        f'Transit EmissionReductionInitiativeInput(pk={transit_emission_reduction_initiative_input.pk})'
        'has been updated.'
    )

    for emission_reduction_initiative_input_data in inputs:
        emission_reduction_initiative_input = EmissionReductionInitiativeInput.objects.get(
            emission_reduction_initiative=emission_reduction_initiative,
            phase=emission_reduction_initiative_input_data['phase'],
            mode=emission_reduction_initiative_input_data['mode'],
        )
        emission_reduction_initiative_input.value = emission_reduction_initiative_input_data['value']
        emission_reduction_initiative_input.save()

        logger.info(f'EmissionReductionInitiativeInput(pk={emission_reduction_initiative_input.pk}) has been updated.')

    return emission_reduction_initiative


def create_emission_management_plan(
    *, user: User, baseline: Baseline, name: str, description: str, version: str, draft: bool
) -> EmissionManagementPlan:
    logger.info(f'User(pk={user.pk}) is creating EmissionManagementPlan for Baseline(pk={baseline.pk}).')

    if EmissionManagementPlan.objects.live().filter(baseline__asset=baseline.asset, name=name).exists():
        raise ValidationError({"name": "EMP name is already used."})

    if baseline.draft:
        raise ValidationError('Baseline is still a draft.')

    emission_management_plan = EmissionManagementPlan.objects.create(
        baseline=baseline,
        name=name,
        description=description,
        version=version,
        draft=draft,
        active=False,
    )

    logger.info(f'EmissionManagementPlan(pk={emission_management_plan.pk}) has been created.')
    return emission_management_plan


def update_emission_management_plan(
    *,
    user: User,
    emission_management_plan: EmissionManagementPlan,
    name: str,
    description: str,
    version: str,
    draft: bool,
) -> EmissionManagementPlan:
    logger.info(f'User(pk={user.pk}) is updating EmissionManagementPlan(pk={emission_management_plan.pk}).')

    if (
        EmissionManagementPlan.objects.live()
        .filter(name=name, baseline__asset=emission_management_plan.baseline.asset)
        .exclude(pk=emission_management_plan.pk)
        .exists()
    ):
        raise ValidationError({"name": "EMP name is already used."})

    emission_management_plan.name = name
    emission_management_plan.description = description
    emission_management_plan.version = version
    emission_management_plan.draft = draft
    if draft and emission_management_plan.active:
        emission_management_plan.active = False
    emission_management_plan.save()

    logger.info(f'EmissionManagementPlan(pk={emission_management_plan.pk}) has been updated.')
    return emission_management_plan


@transaction.atomic
def activate_emission_management_plan(
    *, user: User, emission_management_plan: EmissionManagementPlan
) -> EmissionManagementPlan:
    logger.info(f'User(pk={user.pk}) is activating EmissionManagementPlan(pk={emission_management_plan.pk}).')

    if emission_management_plan.draft:
        raise ValidationError('Energy management plan is still a draft.')

    EmissionManagementPlan.objects.filter(baseline=emission_management_plan.baseline, active=True).update(active=False)
    emission_management_plan.active = True
    emission_management_plan.save()

    logger.info(f'EmissionManagementPlan(pk={emission_management_plan.pk}) has been activated.')
    return emission_management_plan


def duplicate_name(*, old_name: str, max_length: int, check: Callable[[str], bool]) -> str | None:
    suffixes = [' - Copy', f' - Copy - {timezone.now().strftime("%d.%m.%Y %H:%M:%S")}']
    for suffix in suffixes:
        new_name = f'{old_name[:max_length - len(suffix)]}{suffix}'
        if not check(new_name):
            return new_name
    return None


@transaction.atomic
def duplicate_emission_management_plan(
    *,
    user: User,
    emission_management_plan: EmissionManagementPlan,
) -> EmissionManagementPlan:
    logger.info(f'User(pk={user.pk}) is duplicating EmissionManagementPlan(pk={emission_management_plan.pk}).')
    asset = emission_management_plan.baseline.asset

    name_max_length = EmissionManagementPlan._meta.get_field('name').max_length
    emission_management_plan_name = duplicate_name(
        old_name=emission_management_plan.name,
        max_length=name_max_length,
        check=lambda new_name: EmissionManagementPlan.objects.live()
        .filter(baseline__asset=asset)
        .filter(name=new_name)
        .exists(),
    )
    if not emission_management_plan_name:
        raise ValidationError("Unable to duplicate the energy management plan.")

    duplicated_emission_management_plan = EmissionManagementPlan.objects.create(
        baseline=emission_management_plan.baseline,
        name=emission_management_plan_name,
        description=emission_management_plan.description,
        version=emission_management_plan.version,
        draft=True,
        active=False,
    )

    emission_reduction_initiative_name_max_length = EmissionReductionInitiative._meta.get_field('name').max_length

    for emission_reduction_initiative in emission_management_plan.emission_reduction_initiatives.live().order_by('pk'):
        emission_reduction_initiative_name = duplicate_name(
            old_name=emission_reduction_initiative.name,
            max_length=emission_reduction_initiative_name_max_length,
            check=lambda new_name: EmissionReductionInitiative.objects.live()
            .filter(
                emission_management_plan__baseline__asset=asset,
            )
            .filter(name=new_name)
            .exists(),
        )
        if not emission_reduction_initiative_name:
            raise ValidationError("Unable to duplicate the energy reduction initiative.")

        duplicated_emission_reduction_initiative = EmissionReductionInitiative.objects.create(
            emission_management_plan=duplicated_emission_management_plan,
            name=emission_reduction_initiative_name,
            description=emission_reduction_initiative.description,
            type=emission_reduction_initiative.type,
            vendor=emission_reduction_initiative.vendor,
            deployment_date=emission_reduction_initiative.deployment_date,
        )

        EmissionReductionInitiativeInput.objects.bulk_create(
            EmissionReductionInitiativeInput(
                emission_reduction_initiative=duplicated_emission_reduction_initiative,
                phase=emission_reduction_initiative_input.phase,
                mode=emission_reduction_initiative_input.mode,
                value=emission_reduction_initiative_input.value,
            )
            for emission_reduction_initiative_input in emission_reduction_initiative.emission_reduction_initiative_inputs.all()
        )

    logger.info(f'EmissionManagementPlan(pk={emission_management_plan.pk}) has been duplicated.')
    return duplicated_emission_management_plan


def delete_helicopter_type(*, user: User, helicopter_type: HelicopterType) -> HelicopterType:
    logger.info(f'User(pk={user.pk}) is deleting HelicopterType(pk={helicopter_type.pk}).')

    planned_helicopter_use = PlannedHelicopterUse.objects.filter(
        helicopter_type=helicopter_type, well_planner__deleted=False
    ).first()
    if planned_helicopter_use:
        raise ValidationError(
            f"Helicopter type cannot be deleted right now. "
            f"Helicopter type is used by well plan \"{planned_helicopter_use.well_planner.name}\"."
        )

    complete_helicopter_use = CompleteHelicopterUse.objects.filter(
        helicopter_type=helicopter_type, well_planner__deleted=False
    ).first()
    if complete_helicopter_use:
        raise ValidationError(
            f"Helicopter type cannot be deleted right now. "
            f"Helicopter type is used by well plan \"{complete_helicopter_use.well_planner.name}\"."
        )

    helicopter_type.deleted = True
    helicopter_type.save()

    logger.info(f'HelicopterType(pk={helicopter_type.pk}) has been deleted.')
    return helicopter_type


def create_helicopter_type(
    *,
    user: User,
    tenant: Tenant,
    type: str,
    fuel_density: float,
    co2_per_fuel: float,
    nox_per_fuel: float,
    fuel_consumption: float,
    fuel_cost: float,
    co2_tax: float,
    nox_tax: float,
) -> HelicopterType:
    logger.info(f'User(pk={user.pk}) is creating HelicopterType in Tenant(pk={tenant.pk}).')

    helicopter_type = HelicopterType.objects.create(
        tenant=tenant,
        type=type,
        fuel_density=fuel_density,
        co2_per_fuel=co2_per_fuel,
        nox_per_fuel=nox_per_fuel,
        fuel_consumption=fuel_consumption,
        fuel_cost=fuel_cost,
        co2_tax=co2_tax,
        nox_tax=nox_tax,
    )

    logger.info(f'HelicopterType(pk={helicopter_type.pk}) has been created.')
    return helicopter_type


def update_helicopter_type(
    *,
    user: User,
    helicopter_type: HelicopterType,
    type: str,
    fuel_density: float,
    co2_per_fuel: float,
    nox_per_fuel: float,
    fuel_consumption: float,
    fuel_cost: float,
    co2_tax: float,
    nox_tax: float,
) -> HelicopterType:
    logger.info(f'User(pk={user.pk}) is updating HelicopterType(pk={helicopter_type.pk}).')

    helicopter_type.type = type
    helicopter_type.fuel_density = fuel_density
    helicopter_type.co2_per_fuel = co2_per_fuel
    helicopter_type.nox_per_fuel = nox_per_fuel
    helicopter_type.fuel_consumption = fuel_consumption
    helicopter_type.fuel_cost = fuel_cost
    helicopter_type.co2_tax = co2_tax
    helicopter_type.nox_tax = nox_tax
    helicopter_type.save()

    logger.info(f'HelicopterType(pk={helicopter_type.pk}) has been updated.')
    return helicopter_type


@transaction.atomic
def delete_emission_management_plan(
    *,
    user: User,
    emission_management_plan: EmissionManagementPlan,
) -> EmissionManagementPlan:
    logger.info(f'User(pk={user.pk}) is deleting EmissionManagementPlan(pk={emission_management_plan.pk}).')

    if well_plan := emission_management_plan.wellplanner_set.live().first():
        raise ValidationError(
            "Energy management plan cannot be deleted right now. "
            f'Energy management plan is used by well plan "{well_plan.name}".'
        )

    emission_management_plan.deleted = True
    emission_management_plan.active = False
    emission_management_plan.save()

    for emission_reduction_initiative in emission_management_plan.emission_reduction_initiatives.live():
        emission_reduction_initiative.deleted = True
        emission_reduction_initiative.save()
        logger.info("EmissionReductionInitiative(pk={emission_reduction_initiative.pk}) has been deleted.")

    logger.info(f'EmissionManagementPlan(pk={emission_management_plan.pk}) has been deleted.')
    return emission_management_plan


def delete_emission_reduction_initiative(
    *, user: User, emission_reduction_initiative: EmissionReductionInitiative
) -> EmissionReductionInitiative:
    logger.info(f'User(pk={user.pk}) is deleting EmissionReductionInitiative(pk={emission_reduction_initiative.pk}).')

    if well_plan := emission_reduction_initiative.emission_management_plan.wellplanner_set.live().first():
        raise ValidationError(
            "Energy reduction initiative cannot be deleted right now. "
            f'Energy reduction initiative is used by well plan "{well_plan.name}".'
        )

    emission_reduction_initiative.deleted = True
    emission_reduction_initiative.save()

    logger.info(f'EmissionReductionInitiative(pk={emission_reduction_initiative.pk}) has been deleted.')
    return emission_reduction_initiative


def baseline_phases(baseline: Baseline) -> models.QuerySet["CustomPhase"]:
    baseline_inputs = baseline.baselineinput_set.filter(phase=OuterRef('pk'), season=AssetSeason.SUMMER).order_by(
        'order'
    )
    return (
        CustomPhase.objects.filter(asset=baseline.asset)
        .annotate(order=Subquery(baseline_inputs.values('order')[:1]))
        .exclude(order=None)
        .order_by('order')
    )


def baseline_modes(baseline: Baseline) -> models.QuerySet["CustomMode"]:
    baseline_inputs = baseline.baselineinput_set.filter(mode=OuterRef('pk'), season=AssetSeason.SUMMER).order_by(
        'order'
    )
    return (
        CustomMode.objects.filter(asset=baseline.asset)
        .annotate(order=Subquery(baseline_inputs.values('order')[:1]))
        .exclude(order=None)
        .order_by('order')
    )


def delete_material_type(*, user: User, material_type: MaterialType) -> MaterialType:
    logger.info(f'User(pk={user.pk}) is deleting MaterialType(pk={material_type.pk}).')

    if (
        well_planner_step := material_type.planned_steps.select_related('well_planner')  # type: ignore
        .filter(well_planner__deleted=False)
        .first()
        or material_type.complete_steps.select_related('well_planner')  # type: ignore
        .filter(well_planner__deleted=False)
        .first()
    ):
        raise ValidationError(
            "Material type cannot be deleted right now. "
            f'Material type is used by well plan "{well_planner_step.well_planner.name}".'
        )

    material_type.deleted = True
    material_type.save()

    logger.info(f'MaterialType(pk={material_type.pk}) has been deleted.')
    return material_type


def create_material_type(
    *, user: User, tenant: Tenant, category: MaterialCategory, type: str, unit: str, co2: float
) -> MaterialType:
    logger.info(f'User(pk={user.pk}) is creating MaterialType in Tenant(pk={tenant.pk}).')

    material_type = MaterialType.objects.create(
        tenant=tenant,
        category=category,
        type=type,
        unit=unit,
        co2=co2,
        deleted=False,
    )

    logger.info(f'MaterialType(pk={material_type.pk}) has been created.')
    return material_type


def update_material_type(
    *,
    user: User,
    material_type: MaterialType,
    type: str,
    unit: str,
    co2: float,
) -> MaterialType:
    logger.info(f'User(pk={user.pk}) is updating MaterialType(pk={material_type.pk}).')

    material_type.type = type
    material_type.unit = unit
    material_type.co2 = co2
    material_type.save()

    logger.info(f'MaterialType(pk={material_type.pk}) has been updated.')
    return material_type
