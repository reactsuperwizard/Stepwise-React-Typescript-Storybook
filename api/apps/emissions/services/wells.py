import datetime
import logging
import math
from itertools import groupby
from typing import TypedDict, cast

import pytz
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import DateField, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from django_generate_series.models import generate_series

from apps.emissions.models import (
    Asset,
    AssetSeason,
    BaseCO2,
    BaselineCO2,
    BaselineNOX,
    CompleteHelicopterUse,
    CompleteVesselUse,
    EmissionReductionInitiativeType,
    HelicopterType,
    PlannedHelicopterUse,
    PlannedVesselUse,
    TargetCO2,
    TargetCO2Reduction,
    TargetNOX,
    TargetNOXReduction,
    VesselType,
    WellName,
)
from apps.emissions.services.assets import duplicate_name
from apps.emissions.services.calculator import (
    BaselineCO2Data,
    TargetCO2Data,
    calculate_planned_step_baseline_co2,
    calculate_planned_step_baseline_nox,
    calculate_planned_step_target_co2,
    calculate_planned_step_target_nox,
    multiply_baseline_co2,
    multiply_target_co2,
)
from apps.emissions.services.calculator.baseline import BaselineNOXData, multiply_baseline_nox
from apps.emissions.services.calculator.target import TargetNOXData, multiply_target_nox
from apps.tenants.models import Tenant, User
from apps.wells.decorators import require_well_step
from apps.wells.models import (
    WellPlanner,
    WellPlannerPlannedStep,
    WellPlannerPlannedStepEmissionReductionInitiativeRelation,
    WellPlannerWellType,
    WellPlannerWizardStep,
)

logger = logging.getLogger(__name__)


def delete_well(*, user: User, well: WellPlanner) -> WellPlanner:
    logger.info(f"User(pk={user.pk}) is deleting WellPlanner(pk={well.pk}).")

    well.deleted = True
    well.save()

    logger.info(f"WellPlanner(pk={well.pk}) has been deleted.")
    return well


@transaction.atomic
def duplicate_well(*, user: User, well: WellPlanner) -> WellPlanner:
    from apps.wells.services.api import copy_well_planner_step

    logger.info(f"User(pk={user.pk}) is duplicating WellPlanner(pk={well.pk}).")

    sidetrack_length = WellPlanner._meta.get_field('sidetrack').max_length
    duplicated_sidetrack = duplicate_name(
        old_name=well.sidetrack,
        max_length=sidetrack_length,
        check=lambda new_name: WellPlanner.objects.live().filter(name=well.name, sidetrack=new_name).exists(),
    )
    if not duplicated_sidetrack:
        raise ValidationError("Unable to duplicate the well.")

    duplicated_well = WellPlanner.objects.create(
        name=well.name,
        sidetrack=duplicated_sidetrack,
        current_step=WellPlannerWizardStep.WELL_PLANNING,
        actual_start_date=None,
        deleted=False,
        asset=well.asset,
        baseline=well.baseline,
        emission_management_plan=well.emission_management_plan,
        description=well.description,
        type=well.type,
        location=well.location,
        field=well.field,
        planned_start_date=well.planned_start_date,
        fuel_type=well.fuel_type,
        fuel_density=well.fuel_density,
        co2_per_fuel=well.co2_per_fuel,
        nox_per_fuel=well.nox_per_fuel,
        co2_tax=well.co2_tax,
        nox_tax=well.nox_tax,
        fuel_cost=well.fuel_cost,
        boilers_co2_per_fuel=well.boilers_co2_per_fuel,
        boilers_nox_per_fuel=well.boilers_nox_per_fuel,
    )

    for planned_step in well.planned_steps.all():  # type: ignore
        logger.info(f"Duplicating WellPlannerPlannedStep(pk={planned_step.pk}).")
        copy_well_planner_step(
            well_planner_step_class=WellPlannerPlannedStep,
            copy_step=planned_step,
            well_planner=duplicated_well,
            duration=planned_step.duration,
            improved_duration=planned_step.improved_duration,
        )
        logger.info(f"WellPlannerPlannedStep(pk={planned_step.pk}) has been duplicated.")

    for planned_helicopter_use in well.plannedhelicopteruse_set.all():
        logger.info(f"Duplicating PlannedHelicopterUse(pk={planned_helicopter_use.pk}).")
        PlannedHelicopterUse.objects.create(
            well_planner=duplicated_well,
            helicopter_type=planned_helicopter_use.helicopter_type,
            trips=planned_helicopter_use.trips,
            trip_duration=planned_helicopter_use.trip_duration,
            exposure_against_current_well=planned_helicopter_use.exposure_against_current_well,
            quota_obligation=planned_helicopter_use.quota_obligation,
        )
        logger.info(f"PlannedHelicopterUse(pk={planned_helicopter_use.pk}) has been duplicated.")

    for planned_vessel_use in well.plannedvesseluse_set.all():
        logger.info(f"Duplicating PlannedVesselUse(pk={planned_vessel_use.pk}).")
        PlannedVesselUse.objects.create(
            well_planner=duplicated_well,
            vessel_type=planned_vessel_use.vessel_type,
            duration=planned_vessel_use.duration,
            exposure_against_current_well=planned_vessel_use.exposure_against_current_well,
            waiting_on_weather=planned_vessel_use.waiting_on_weather,
            season=planned_vessel_use.season,
            quota_obligation=planned_vessel_use.quota_obligation,
        )
        logger.info(f"PlannedVesselUse(pk={planned_vessel_use.pk}) has been duplicated.")

    logger.info(f"WellPlanner(pk={well.pk}) has been duplicated.")

    calculate_planned_emissions(duplicated_well)

    return duplicated_well


def validate_well_data(*, tenant: Tenant, asset: Asset, name: WellName) -> None:
    if tenant.pk != asset.tenant_id:
        logger.error(f'Invalid well data. Asset(pk={asset.pk}) does not belong to Tenant(pk={tenant.pk}).')
        raise ValidationError({"asset": "Chosen asset is not a valid choice."})

    if tenant.pk != name.tenant_id:
        logger.error(f'Invalid well data. WellName(pk={name.pk}) does not belong to Tenant(pk={tenant.pk}).')
        raise ValidationError({"name": "Chosen name is not a valid choice."})

    if asset.deleted:
        logger.error(f'Invalid well data. Asset(pk={asset.pk}) is deleted.')
        raise ValidationError({"asset": "Chosen asset is not a valid choice."})

    if asset.draft:
        logger.error(f'Invalid well data. Asset(pk={asset.pk}) is draft.')
        raise ValidationError({"asset": "Chosen asset is not a valid choice."})


def create_well(
    *,
    tenant: Tenant,
    user: User,
    name: WellName,
    sidetrack: str,
    description: str,
    field: str,
    location: str,
    type: WellPlannerWellType,
    asset: Asset,
    fuel_type: str,
    fuel_density: float,
    co2_per_fuel: float,
    nox_per_fuel: float,
    co2_tax: float,
    nox_tax: float,
    fuel_cost: float,
    boilers_co2_per_fuel: float,
    boilers_nox_per_fuel: float,
) -> WellPlanner:
    logger.info(f'User(pk={user.pk}) is creating WellPlanner.')

    validate_well_data(tenant=tenant, asset=asset, name=name)

    if WellPlanner.objects.live().filter(name=name, sidetrack=sidetrack).exists():
        raise ValidationError({"name": "Well name and sidetrack are already used."})

    baseline = asset.baselines.get(active=True)
    emission_management_plan = baseline.emission_management_plans.filter(active=True).first()

    well = WellPlanner.objects.create(
        current_step=WellPlannerWizardStep.WELL_PLANNING,
        asset=asset,
        baseline=baseline,
        emission_management_plan=emission_management_plan,
        name=name,
        sidetrack=sidetrack,
        description=description,
        field=field,
        location=location,
        type=type,
        fuel_type=fuel_type,
        fuel_density=fuel_density,
        co2_per_fuel=co2_per_fuel,
        nox_per_fuel=nox_per_fuel,
        co2_tax=co2_tax,
        nox_tax=nox_tax,
        fuel_cost=fuel_cost,
        boilers_co2_per_fuel=boilers_co2_per_fuel,
        boilers_nox_per_fuel=boilers_nox_per_fuel,
        planned_start_date=timezone.now().date(),
    )

    logger.info(f'WellPlanner(pk={well.pk}) has been created.')
    return well


@transaction.atomic
@require_well_step(
    allowed_steps=[WellPlannerWizardStep.WELL_PLANNING],
    error='Well cannot be updated right now.',
)
def update_well(
    *,
    well_planner: WellPlanner,
    user: User,
    name: WellName,
    sidetrack: str,
    description: str,
    field: str,
    location: str,
    type: WellPlannerWellType,
    asset: Asset,
    fuel_type: str,
    fuel_density: float,
    co2_per_fuel: float,
    nox_per_fuel: float,
    co2_tax: float,
    nox_tax: float,
    fuel_cost: float,
    boilers_co2_per_fuel: float,
    boilers_nox_per_fuel: float,
) -> WellPlanner:
    logger.info(f'User(pk={user.pk}) is updating WellPlanner(pk={well_planner.pk}).')

    old_asset = well_planner.asset
    baseline = well_planner.baseline
    emission_management_plan = well_planner.emission_management_plan

    validate_well_data(tenant=old_asset.tenant, asset=asset, name=name)

    if WellPlanner.objects.live().filter(name=name, sidetrack=sidetrack).exclude(pk=well_planner.pk).exists():
        raise ValidationError({"name": "Well name and sidetrack are already used."})

    if asset != old_asset:
        if WellPlannerPlannedStep.objects.filter(well_planner=well_planner).exists():
            raise ValidationError({"asset": "Asset cannot be changed for a well with existing phases."})

        baseline = asset.baselines.get(active=True)
        emission_management_plan = baseline.emission_management_plans.filter(active=True).first()

    well_planner.asset = asset
    well_planner.baseline = baseline
    well_planner.emission_management_plan = emission_management_plan
    well_planner.name = name
    well_planner.sidetrack = sidetrack
    well_planner.description = description
    well_planner.field = field
    well_planner.location = location
    well_planner.type = type
    well_planner.fuel_type = fuel_type
    well_planner.fuel_density = fuel_density
    well_planner.co2_per_fuel = co2_per_fuel
    well_planner.nox_per_fuel = nox_per_fuel
    well_planner.co2_tax = co2_tax
    well_planner.nox_tax = nox_tax
    well_planner.fuel_cost = fuel_cost
    well_planner.boilers_co2_per_fuel = boilers_co2_per_fuel
    well_planner.boilers_nox_per_fuel = boilers_nox_per_fuel
    well_planner.save()

    logger.info(f'WellPlanner(pk={well_planner.pk}) has been updated.')

    calculate_planned_emissions(well_planner)

    return well_planner


def create_well_name(*, user: User, tenant: Tenant, name: str) -> WellName:
    logger.info(f'User(pk={user.pk}) is creating WellName.')

    if WellName.objects.filter(tenant=tenant, name=name).exists():
        raise ValidationError({"name": "Well name is already used."})

    well_name = WellName.objects.create(tenant=tenant, name=name)
    logger.info(f'WellName(pk={well_name.pk}) has been created.')
    return well_name


@transaction.atomic
@require_well_step(
    allowed_steps=[
        WellPlannerWizardStep.WELL_PLANNING,
    ],
    error='Vessel cannot be created right now.',
)
def create_planned_vessel_use(
    *,
    user: User,
    well_planner: WellPlanner,
    vessel_type: VesselType,
    duration: float,
    exposure_against_current_well: float,
    waiting_on_weather: float,
    season: AssetSeason,
    quota_obligation: float,
) -> PlannedVesselUse:
    logger.info(f"User(pk={user}) is creating planned vessel use for WellPlanner(pk={well_planner.pk}).")

    if not VesselType.objects.live().filter(tenant=well_planner.asset.tenant_id, pk=vessel_type.pk).exists():
        logger.info(
            f"Unable to find VesselType(pk={vessel_type.pk}, tenant={well_planner.asset.tenant_id}, deleted=False)."
        )
        raise ValidationError({"vessel_type": "Chosen vessel is not a valid choice."})

    planned_vessel_use = PlannedVesselUse.objects.create(
        well_planner=well_planner,
        vessel_type=vessel_type,
        duration=duration,
        exposure_against_current_well=exposure_against_current_well,
        waiting_on_weather=waiting_on_weather,
        season=season,
        quota_obligation=quota_obligation,
    )

    logger.info(f"PlannedVesselUse(pk={planned_vessel_use.pk}) has been created.")

    calculate_planned_emissions(well_planner)

    return planned_vessel_use


@transaction.atomic
@require_well_step(
    allowed_steps=[
        WellPlannerWizardStep.WELL_PLANNING,
    ],
    get_well=lambda *args, **kwargs: kwargs['planned_vessel_use'].well_planner,
    error='Vessel cannot be updated right now.',
)
def update_planned_vessel_use(
    *,
    user: User,
    planned_vessel_use: PlannedVesselUse,
    vessel_type: VesselType,
    duration: float,
    exposure_against_current_well: float,
    waiting_on_weather: float,
    season: AssetSeason,
    quota_obligation: float,
) -> PlannedVesselUse:
    logger.info(f"User(pk={user}) is updating PlannedVesselUse(pk={planned_vessel_use.pk}).")

    if (
        not VesselType.objects.live()
        .filter(tenant=planned_vessel_use.well_planner.asset.tenant_id, pk=vessel_type.pk)
        .exists()
    ):
        logger.info(
            f"Unable to find VesselType(pk={vessel_type.pk}, tenant={planned_vessel_use.well_planner.asset.tenant_id}, deleted=False)."
        )
        raise ValidationError({"vessel_type": "Chosen vessel is not a valid choice."})

    planned_vessel_use.vessel_type = vessel_type
    planned_vessel_use.duration = duration
    planned_vessel_use.exposure_against_current_well = exposure_against_current_well
    planned_vessel_use.waiting_on_weather = waiting_on_weather
    planned_vessel_use.season = season
    planned_vessel_use.quota_obligation = quota_obligation
    planned_vessel_use.save()

    logger.info(f"PlannedVesselUse(pk={planned_vessel_use.pk}) has been updated.")

    calculate_planned_emissions(planned_vessel_use.well_planner)

    return planned_vessel_use


@transaction.atomic
@require_well_step(
    allowed_steps=[
        WellPlannerWizardStep.WELL_PLANNING,
    ],
    get_well=lambda *args, **kwargs: kwargs['planned_vessel_use'].well_planner,
    error='Vessel cannot be deleted right now.',
)
def delete_planned_vessel_use(*, user: User, planned_vessel_use: PlannedVesselUse) -> None:
    logger.info(f"User(pk={user}) is deleting PlannedVesselUse(pk={planned_vessel_use.pk}).")
    well_plan = planned_vessel_use.well_planner

    planned_vessel_use.delete()

    logger.info(f"PlannedVesselUse(pk={planned_vessel_use.pk}) has been deleted.")

    calculate_planned_emissions(well_plan)


@transaction.atomic
@require_well_step(
    allowed_steps=[
        WellPlannerWizardStep.WELL_REVIEWING,
    ],
    error='Vessel cannot be created right now.',
)
def create_complete_vessel_use(
    *,
    user: User,
    well_planner: WellPlanner,
    vessel_type: VesselType,
    duration: float,
    exposure_against_current_well: float,
    waiting_on_weather: float,
    season: AssetSeason,
    quota_obligation: float,
) -> CompleteVesselUse:
    logger.info(f"User(pk={user}) is creating complete vessel use for WellPlanner(pk={well_planner.pk}).")

    if not VesselType.objects.live().filter(tenant=well_planner.asset.tenant_id, pk=vessel_type.pk).exists():
        logger.info(
            f"Unable to find VesselType(pk={vessel_type.pk}, tenant={well_planner.asset.tenant_id}, deleted=False)."
        )
        raise ValidationError({"vessel_type": "Chosen vessel is not a valid choice."})

    complete_vessel_use = CompleteVesselUse.objects.create(
        well_planner=well_planner,
        vessel_type=vessel_type,
        duration=duration,
        exposure_against_current_well=exposure_against_current_well,
        waiting_on_weather=waiting_on_weather,
        season=season,
        quota_obligation=quota_obligation,
        approved=False,
    )

    logger.info(f"CompleteVesselUse(pk={complete_vessel_use.pk}) has been created.")
    return complete_vessel_use


@transaction.atomic
@require_well_step(
    allowed_steps=[
        WellPlannerWizardStep.WELL_REVIEWING,
    ],
    get_well=lambda *args, **kwargs: kwargs['complete_vessel_use'].well_planner,
    error='Vessel cannot be updated right now.',
)
def update_complete_vessel_use(
    *,
    user: User,
    complete_vessel_use: CompleteVesselUse,
    vessel_type: VesselType,
    duration: float,
    exposure_against_current_well: float,
    waiting_on_weather: float,
    season: AssetSeason,
    quota_obligation: float,
) -> CompleteVesselUse:
    logger.info(f"User(pk={user}) is updating CompleteVesselUse(pk={complete_vessel_use.pk}).")

    if (
        not VesselType.objects.live()
        .filter(tenant=complete_vessel_use.well_planner.asset.tenant_id, pk=vessel_type.pk)
        .exists()
    ):
        logger.info(
            f"Unable to find VesselType(pk={vessel_type.pk}, tenant={complete_vessel_use.well_planner.asset.tenant_id}, deleted=False)."
        )
        raise ValidationError({"vessel_type": "Chosen vessel is not a valid choice."})

    complete_vessel_use.vessel_type = vessel_type
    complete_vessel_use.duration = duration
    complete_vessel_use.exposure_against_current_well = exposure_against_current_well
    complete_vessel_use.waiting_on_weather = waiting_on_weather
    complete_vessel_use.season = season
    complete_vessel_use.quota_obligation = quota_obligation
    complete_vessel_use.approved = False
    complete_vessel_use.save()

    logger.info(f"CompleteVesselUse(pk={complete_vessel_use.pk}) has been updated.")
    return complete_vessel_use


@transaction.atomic
@require_well_step(
    allowed_steps=[
        WellPlannerWizardStep.WELL_REVIEWING,
    ],
    get_well=lambda *args, **kwargs: kwargs['complete_vessel_use'].well_planner,
    error='Vessel cannot be deleted right now.',
)
def delete_complete_vessel_use(*, user: User, complete_vessel_use: CompleteVesselUse) -> None:
    logger.info(f"User(pk={user}) is deleting CompleteVesselUse(pk={complete_vessel_use.pk}).")

    complete_vessel_use.delete()

    logger.info(f"CompleteVesselUse(pk={complete_vessel_use.pk}) has been deleted.")


@transaction.atomic
@require_well_step(
    allowed_steps=[
        WellPlannerWizardStep.WELL_PLANNING,
    ],
    error='Planned start date cannot be updated right now.',
)
def update_well_planned_start_date(
    *, user: User, well_planner: WellPlanner, planned_start_date: datetime.date
) -> WellPlanner:
    logger.info(f"User(pk={user.pk}) is updating planned start date for WellPlanner(pk={well_planner.pk})")

    invalid_eri_relation = (
        WellPlannerPlannedStepEmissionReductionInitiativeRelation.objects.filter(
            wellplannerplannedstep__well_planner=well_planner,
            emissionreductioninitiative__deployment_date__gt=planned_start_date,
        )
        .select_related('emissionreductioninitiative')
        .first()
    )
    if invalid_eri_relation:
        raise ValidationError(
            "Unable to change planned start date. "
            f"Energy reduction initiative \"{invalid_eri_relation.emissionreductioninitiative.name}\" won't be "
            f"deployed until that date."
        )

    well_planner.planned_start_date = planned_start_date
    well_planner.save()

    logger.info("Planned start date has been changed.")

    calculate_planned_emissions(well_planner)

    return well_planner


def validate_helicopter_use_data(*, tenant: Tenant, helicopter_type: HelicopterType) -> None:
    if not HelicopterType.objects.live().filter(tenant=tenant, pk=helicopter_type.pk).exists():
        logger.info(
            f"Unable to validate helicopter use data. "
            f"HelicopterType(pk={helicopter_type.pk}, tenant={tenant}, deleted=False) doesn't exist."
        )
        raise ValidationError({"helicopter_type": "Chosen helicopter is not a valid choice."})


@transaction.atomic
@require_well_step(
    allowed_steps=[
        WellPlannerWizardStep.WELL_PLANNING,
    ],
    error='Helicopter cannot be created right now.',
)
def create_planned_helicopter_use(
    *,
    user: User,
    well_planner: WellPlanner,
    helicopter_type: HelicopterType,
    trips: int,
    trip_duration: int,
    exposure_against_current_well: float,
    quota_obligation: float,
) -> PlannedHelicopterUse:
    logger.info(f"User(pk={user}) is creating planned helicopter use for WellPlanner(pk={well_planner.pk}).")

    validate_helicopter_use_data(tenant=well_planner.asset.tenant, helicopter_type=helicopter_type)

    planned_helicopter_use = PlannedHelicopterUse.objects.create(
        well_planner=well_planner,
        helicopter_type=helicopter_type,
        trips=trips,
        trip_duration=trip_duration,
        exposure_against_current_well=exposure_against_current_well,
        quota_obligation=quota_obligation,
    )

    logger.info(f"PlannedHelicopterUse(pk={planned_helicopter_use.pk}) has been created.")

    calculate_planned_emissions(well_planner)

    return planned_helicopter_use


@transaction.atomic
@require_well_step(
    allowed_steps=[
        WellPlannerWizardStep.WELL_PLANNING,
    ],
    get_well=lambda *args, **kwargs: kwargs['planned_helicopter_use'].well_planner,
    error='Helicopter cannot be updated right now.',
)
def update_planned_helicopter_use(
    *,
    user: User,
    planned_helicopter_use: PlannedHelicopterUse,
    helicopter_type: HelicopterType,
    trips: int,
    trip_duration: int,
    exposure_against_current_well: float,
    quota_obligation: float,
) -> PlannedHelicopterUse:
    logger.info(f"User(pk={user}) is updating PlannedHelicopterUse(pk={planned_helicopter_use.pk}).")

    validate_helicopter_use_data(
        tenant=planned_helicopter_use.well_planner.asset.tenant, helicopter_type=helicopter_type
    )

    planned_helicopter_use.helicopter_type = helicopter_type
    planned_helicopter_use.trips = trips
    planned_helicopter_use.trip_duration = trip_duration
    planned_helicopter_use.exposure_against_current_well = exposure_against_current_well
    planned_helicopter_use.quota_obligation = quota_obligation
    planned_helicopter_use.save()

    logger.info(f"PlannedHelicopterUse(pk={planned_helicopter_use.pk}) has been updated.")

    calculate_planned_emissions(planned_helicopter_use.well_planner)

    return planned_helicopter_use


@transaction.atomic
@require_well_step(
    allowed_steps=[
        WellPlannerWizardStep.WELL_PLANNING,
    ],
    get_well=lambda *args, **kwargs: kwargs['planned_helicopter_use'].well_planner,
    error='Helicopter cannot be deleted right now.',
)
def delete_planned_helicopter_use(
    *,
    user: User,
    planned_helicopter_use: PlannedHelicopterUse,
) -> None:
    logger.info(f"User(pk={user}) is deleting PlannedHelicopterUse(pk={planned_helicopter_use.pk}).")
    well_plan = planned_helicopter_use.well_planner

    planned_helicopter_use.delete()

    logger.info(f"PlannedHelicopterUse(pk={planned_helicopter_use.pk}) has been deleted.")

    calculate_planned_emissions(well_plan)


@transaction.atomic
@require_well_step(
    allowed_steps=[
        WellPlannerWizardStep.WELL_REVIEWING,
    ],
    error='Helicopter cannot be created right now.',
)
def create_complete_helicopter_use(
    *,
    user: User,
    well_planner: WellPlanner,
    helicopter_type: HelicopterType,
    trips: int,
    trip_duration: int,
    exposure_against_current_well: float,
    quota_obligation: float,
) -> CompleteHelicopterUse:
    logger.info(f"User(pk={user}) is creating complete helicopter use for WellPlanner(pk={well_planner.pk}).")

    validate_helicopter_use_data(tenant=well_planner.asset.tenant, helicopter_type=helicopter_type)

    complete_helicopter_use = CompleteHelicopterUse.objects.create(
        well_planner=well_planner,
        helicopter_type=helicopter_type,
        trips=trips,
        trip_duration=trip_duration,
        exposure_against_current_well=exposure_against_current_well,
        quota_obligation=quota_obligation,
        approved=False,
    )

    logger.info(f"CompleteHelicopterUse(pk={complete_helicopter_use.pk}) has been created.")
    return complete_helicopter_use


@transaction.atomic
@require_well_step(
    allowed_steps=[
        WellPlannerWizardStep.WELL_REVIEWING,
    ],
    get_well=lambda *args, **kwargs: kwargs['complete_helicopter_use'].well_planner,
    error='Helicopter cannot be updated right now.',
)
def update_complete_helicopter_use(
    *,
    user: User,
    complete_helicopter_use: CompleteHelicopterUse,
    helicopter_type: HelicopterType,
    trips: int,
    trip_duration: int,
    exposure_against_current_well: float,
    quota_obligation: float,
) -> CompleteHelicopterUse:
    logger.info(f"User(pk={user}) is updating CompleteHelicopterUse(pk={complete_helicopter_use.pk}).")

    validate_helicopter_use_data(
        tenant=complete_helicopter_use.well_planner.asset.tenant,
        helicopter_type=helicopter_type,
    )

    complete_helicopter_use.helicopter_type = helicopter_type
    complete_helicopter_use.trips = trips
    complete_helicopter_use.trip_duration = trip_duration
    complete_helicopter_use.exposure_against_current_well = exposure_against_current_well
    complete_helicopter_use.quota_obligation = quota_obligation
    complete_helicopter_use.approved = False
    complete_helicopter_use.save()

    logger.info(f"CompleteHelicopterUse(pk={complete_helicopter_use.pk}) has been updated.")
    return complete_helicopter_use


@transaction.atomic
@require_well_step(
    allowed_steps=[
        WellPlannerWizardStep.WELL_REVIEWING,
    ],
    get_well=lambda *args, **kwargs: kwargs['complete_helicopter_use'].well_planner,
    error='Helicopter cannot be deleted right now.',
)
def delete_complete_helicopter_use(*, user: User, complete_helicopter_use: CompleteHelicopterUse) -> None:
    logger.info(f"User(pk={user}) is deleting CompleteHelicopterUse(pk={complete_helicopter_use.pk}).")

    complete_helicopter_use.delete()

    logger.info(f"CompleteHelicopterUse(pk={complete_helicopter_use.pk}) has been deleted.")


def save_baseline_co2(
    *, planned_step: WellPlannerPlannedStep, datetime: datetime.datetime, baseline_data: BaselineCO2Data
) -> BaselineCO2:
    logger.info(f"Creating BaselineCO2 entry for WellPlannerPlannedStep(pk={planned_step.pk}).")
    baseline_co2 = BaselineCO2.objects.create(
        planned_step=planned_step,
        datetime=datetime,
        asset=baseline_data['asset'],
        boilers=baseline_data['boilers'],
        vessels=baseline_data['vessels'],
        helicopters=baseline_data['helicopters'],
        materials=baseline_data['materials'],
        external_energy_supply=baseline_data['external_energy_supply'],
    )

    logger.info(f"BaselineCO2(pk={baseline_co2.pk}) has been created.")
    return baseline_co2


def save_baseline_nox(
    *, planned_step: WellPlannerPlannedStep, datetime: datetime.datetime, baseline_data: BaselineNOXData
) -> BaselineNOX:
    logger.info(f"Creating BaselineNOX entry for WellPlannerPlannedStep(pk={planned_step.pk}).")
    baseline_nox = BaselineNOX.objects.create(
        planned_step=planned_step,
        datetime=datetime,
        asset=baseline_data['asset'],
        boilers=baseline_data['boilers'],
        vessels=baseline_data['vessels'],
        helicopters=baseline_data['helicopters'],
        external_energy_supply=baseline_data['external_energy_supply'],
    )

    logger.info(f"BaselineNOX(pk={baseline_nox.pk}) has been created.")
    return baseline_nox


def save_target_co2(
    *, planned_step: WellPlannerPlannedStep, datetime: datetime.datetime, target_data: TargetCO2Data
) -> TargetCO2:
    logger.info(f"Creating TargetCO2 entry for WellPlannerPlannedStep(pk={planned_step.pk}).")
    target_co2 = TargetCO2.objects.create(
        planned_step=planned_step,
        datetime=datetime,
        asset=target_data['asset'],
        boilers=target_data['boilers'],
        vessels=target_data['vessels'],
        helicopters=target_data['helicopters'],
        materials=target_data['materials'],
        external_energy_supply=target_data['external_energy_supply'],
    )
    TargetCO2Reduction.objects.bulk_create(
        [
            TargetCO2Reduction(
                target=target_co2,
                emission_reduction_initiative_id=target_co2_reduction_data['emission_reduction_initiative_id'],
                value=target_co2_reduction_data['value'],
            )
            for target_co2_reduction_data in target_data['emission_reduction_initiatives']
        ]
    )

    logger.info(f"TargetCO2(pk={target_co2.pk}) has been created.")
    return target_co2


def save_target_nox(
    *, planned_step: WellPlannerPlannedStep, datetime: datetime.datetime, target_data: TargetNOXData
) -> TargetNOX:
    logger.info(f"Creating TargetNOX entry for WellPlannerPlannedStep(pk={planned_step.pk}).")
    target_nox = TargetNOX.objects.create(
        planned_step=planned_step,
        datetime=datetime,
        asset=target_data['asset'],
        boilers=target_data['boilers'],
        vessels=target_data['vessels'],
        helicopters=target_data['helicopters'],
        external_energy_supply=target_data['external_energy_supply'],
    )
    TargetNOXReduction.objects.bulk_create(
        [
            TargetNOXReduction(
                target=target_nox,
                emission_reduction_initiative_id=target_nox_reduction_data['emission_reduction_initiative_id'],
                value=target_nox_reduction_data['value'],
            )
            for target_nox_reduction_data in target_data['emission_reduction_initiatives']
        ]
    )

    logger.info(f"TargetNOX(pk={target_nox.pk}) has been created.")
    return target_nox


def calculate_baselines(*, well_plan: WellPlanner) -> None:
    from apps.wells.services.api import split_duration_into_days

    logger.info(f"Calculating baselines for WellPlan(pk=${well_plan.pk}).")
    BaselineCO2.objects.filter(planned_step__well_planner=well_plan).delete()
    BaselineNOX.objects.filter(planned_step__well_planner=well_plan).delete()

    planned_steps = well_plan.planned_steps.order_by('order')  # type: ignore

    plan_duration = sum(planned_step.duration for planned_step in planned_steps)
    season_durations = {
        AssetSeason.WINTER: sum(
            planned_step.duration for planned_step in planned_steps if planned_step.season == AssetSeason.WINTER
        ),
        AssetSeason.SUMMER: sum(
            planned_step.duration for planned_step in planned_steps if planned_step.season == AssetSeason.SUMMER
        ),
    }

    plan_start_date = datetime.datetime(
        day=well_plan.planned_start_date.day,
        month=well_plan.planned_start_date.month,
        year=well_plan.planned_start_date.year,
        tzinfo=pytz.UTC,
    )

    processed_duration = 0.0

    for planned_step in planned_steps:
        baseline_co2 = calculate_planned_step_baseline_co2(
            planned_step=planned_step,
            step_duration=planned_step.duration,
            plan_duration=plan_duration,
            season_duration=season_durations[planned_step.season],
        )
        daily_baseline_co2 = multiply_baseline_co2(baseline=baseline_co2, multiplier=1 / planned_step.duration)

        baseline_nox = calculate_planned_step_baseline_nox(
            planned_step=planned_step,
            step_duration=planned_step.duration,
            plan_duration=plan_duration,
            season_duration=season_durations[planned_step.season],
        )
        daily_baseline_nox = multiply_baseline_nox(baseline=baseline_nox, multiplier=1 / planned_step.duration)

        for day_date, day_duration in split_duration_into_days(
            start_date=plan_start_date,
            total_days=processed_duration,
            duration=planned_step.duration,
        ):
            baseline_co2_for_day = multiply_baseline_co2(baseline=daily_baseline_co2, multiplier=day_duration)
            save_baseline_co2(
                planned_step=planned_step,
                datetime=day_date,
                baseline_data=baseline_co2_for_day,
            )

            baseline_nox_for_day = multiply_baseline_nox(baseline=daily_baseline_nox, multiplier=day_duration)
            save_baseline_nox(
                planned_step=planned_step,
                datetime=day_date,
                baseline_data=baseline_nox_for_day,
            )

            processed_duration += day_duration

    logger.info(f"Baselines for WellPlan(pk=${well_plan.pk}) have been calculated.")


def calculate_targets(*, well_plan: WellPlanner) -> None:
    from apps.wells.services.api import split_duration_into_days

    logger.info(f"Calculating targets for WellPlan(pk=${well_plan.pk}).")
    TargetCO2.objects.filter(planned_step__well_planner=well_plan).delete()
    TargetNOX.objects.filter(planned_step__well_planner=well_plan).delete()

    planned_steps = well_plan.planned_steps.order_by('order')  # type: ignore
    plan_start_date = datetime.datetime(
        day=well_plan.planned_start_date.day,
        month=well_plan.planned_start_date.month,
        year=well_plan.planned_start_date.year,
        tzinfo=pytz.UTC,
    )

    target_plan_duration = sum(planned_step.improved_duration for planned_step in planned_steps)
    target_season_duration = {
        season: sum(planned_step.improved_duration for planned_step in planned_steps if planned_step.season == season)
        for season in AssetSeason
    }
    processed_target_duration = 0.0

    for planned_step in planned_steps:
        target_step_duration = planned_step.improved_duration

        target_co2 = calculate_planned_step_target_co2(
            planned_step=planned_step,
            step_duration=target_step_duration,
            plan_duration=target_plan_duration,
            season_duration=target_season_duration[planned_step.season],
        )
        daily_target_co2 = multiply_target_co2(target=target_co2, multiplier=1 / target_step_duration)

        target_nox = calculate_planned_step_target_nox(
            planned_step=planned_step,
            step_duration=target_step_duration,
            plan_duration=target_plan_duration,
            season_duration=target_season_duration[planned_step.season],
        )
        daily_target_nox = multiply_target_nox(target=target_nox, multiplier=1 / target_step_duration)

        for day_date, day_duration in split_duration_into_days(
            start_date=plan_start_date,
            total_days=processed_target_duration,
            duration=target_step_duration,
        ):
            target_co2_for_day = multiply_target_co2(target=daily_target_co2, multiplier=day_duration)
            save_target_co2(
                planned_step=planned_step,
                datetime=day_date,
                target_data=target_co2_for_day,
            )

            target_nox_for_day = multiply_target_nox(target=daily_target_nox, multiplier=day_duration)
            save_target_nox(
                planned_step=planned_step,
                datetime=day_date,
                target_data=target_nox_for_day,
            )

            processed_target_duration += day_duration

    logger.info(f"Targets have been calculated for WellPlan(pk=${well_plan.pk}).")


@transaction.atomic
def calculate_planned_emissions(well_plan: WellPlanner) -> None:
    if well_plan.current_step != WellPlannerWizardStep.WELL_PLANNING:
        raise ValueError("Unable to calculate planned emissions")

    logger.info(f"Calculating planned emissions for WellPlan(pk=${well_plan.pk}).")

    calculate_baselines(well_plan=well_plan)
    calculate_targets(well_plan=well_plan)

    logger.info(f"Calculated planned emissions for WellPlan(pk=${well_plan.pk}).")


def get_co2_emissions(well_planner: WellPlanner, co2_model: type[BaseCO2]) -> models.QuerySet[BaseCO2]:
    return cast(
        models.QuerySet[BaseCO2],
        (
            co2_model.objects.filter(planned_step__well_planner=well_planner)
            .annotate(date=TruncDate('datetime'))
            .values('date')
            .annotate(
                total_asset=Sum('asset'),
                total_external_energy_supply=Sum('external_energy_supply'),
                total_vessels=Sum('vessels'),
                total_helicopters=Sum('helicopters'),
                total_materials=Sum('materials'),
                total_boilers=Sum('boilers'),
            )
            .order_by('date')
        ),
    )


class EmissionReductionInitiativeReduction(TypedDict):
    date: datetime.date
    emission_reduction_initiative: int
    emission_reduction_initiative__type: EmissionReductionInitiativeType
    emission_reduction_initiative__name: str
    total_value: float


class EmissionReduction(TypedDict):
    date: datetime.date
    emission_reduction_initiatives: list[EmissionReductionInitiativeReduction]


def get_emission_reductions(
    well_plan: WellPlanner, reduction_model: type[TargetCO2Reduction]
) -> list[EmissionReduction]:
    from apps.wells.services.api import get_well_planner_planned_duration

    emission_reduction_initiatives = (
        reduction_model.objects.filter(target__planned_step__well_planner=well_plan)
        .annotate(date=TruncDate('target__datetime'))
        .values(
            'date',
            'emission_reduction_initiative',
            'emission_reduction_initiative__type',
            'emission_reduction_initiative__name',
        )
        .annotate(total_value=Sum('value'))
        .order_by('date', 'emission_reduction_initiative')
    )

    _, duration = get_well_planner_planned_duration(well_plan)
    plan_end_date = well_plan.planned_start_date + datetime.timedelta(
        days=math.ceil(duration) - 1 if duration else duration
    )

    emission_reductions = dict()
    for row in generate_series(well_plan.planned_start_date, plan_end_date, "1 days", output_field=DateField):
        emission_reductions[row.term] = dict(date=row.term, emission_reduction_initiatives=[])

    for date, daily_reductions in groupby(
        emission_reduction_initiatives, lambda initiative: cast(datetime.date, initiative['date'])
    ):
        emission_reductions[date] = dict(date=date, emission_reduction_initiatives=list(daily_reductions))

    return cast(list[EmissionReduction], list(emission_reductions.values()))
