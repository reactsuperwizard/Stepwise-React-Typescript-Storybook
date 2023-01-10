import datetime
import logging
from typing import Any, Generator, TypedDict, TypeVar, cast

import pytz
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Avg, DateTimeField, F, FloatField, OuterRef, QuerySet, Subquery
from django.db.models.functions import Coalesce
from django_generate_series.models import generate_series

from apps.emissions.models import (
    AssetSeason,
    BaselineInput,
    CompleteHelicopterUse,
    CompleteVesselUse,
    CustomMode,
    CustomPhase,
    EmissionReductionInitiative,
)
from apps.emissions.models.assets import MaterialType
from apps.emissions.services.wells import calculate_planned_emissions
from apps.monitors.models import MonitorFunctionType, MonitorFunctionValue
from apps.projects.models import Project
from apps.rigs.tasks import sync_all_custom_well_co2_calculations_task, sync_all_plan_co2_calculations_task
from apps.tenants.models import Tenant, User
from apps.wells.decorators import require_well_step
from apps.wells.models import (
    BaseWellPlannerStep,
    CustomWell,
    WellPlanner,
    WellPlannerCompleteStep,
    WellPlannerPlannedStep,
    WellPlannerWizardStep,
)
from apps.wells.services.co2calculator import (
    WellPlannerStepCO2EmissionReductionInitiative,
    WellPlannerStepCO2Result,
    calculate_measured_well_planner_step_co2,
    calculate_planned_step_improved_duration,
    calculate_well_planner_co2_improvement,
    calculate_well_planner_step_co2,
    get_seasons_duration,
    multiply_well_planner_step_co2,
)

logger = logging.getLogger(__name__)


class WellPlannerStepCo2Dataset(TypedDict):
    date: datetime.date
    step: BaseWellPlannerStep
    base: float
    baseline: float
    target: float
    rig: float
    vessels: float
    helicopters: float
    cement: float
    steel: float
    external_energy_supply: float
    emission_reduction_initiatives: list[WellPlannerStepCO2EmissionReductionInitiative]


class WellPlannerCo2Dataset(TypedDict):
    date: datetime.date
    base: float
    baseline: float
    target: float
    rig: float
    vessels: float
    helicopters: float
    cement: float
    steel: float
    external_energy_supply: float
    emission_reduction_initiatives: list[WellPlannerStepCO2EmissionReductionInitiative]


class WellPlannerMeasurementDataset(TypedDict):
    date: datetime.date
    value: float


class WellPlannerSummary(TypedDict):
    total_baseline: float
    total_target: float
    total_improved_duration: float


class WellPlannerMeasuredSummary(TypedDict):
    total_baseline: float
    total_target: float
    total_duration: float


class WellPlannerStepMaterialData(TypedDict):
    id: int | None
    material_type: MaterialType
    quantity: float
    quota: bool


@transaction.atomic
def create_custom_well(tenant: Tenant, user: User, **data: Any) -> CustomWell:
    logger.info(f'User(pk={user.pk}) is creating a new custom well in Tenant(pk={tenant.pk})')
    project_id = data.pop('project', None)
    project = None
    if project_id:
        try:
            project = Project.objects.get(tenant=tenant, pk=cast(int, project_id))
        except Project.DoesNotExist:
            raise ValidationError({"project": f'Project {project_id} doesn\'t exist'})
    well = CustomWell.objects.create(
        tenant=tenant,
        creator=user,
        **data,
    )
    logger.info(f'CustomWell(pk={well.pk}) has been created')
    if project:
        project.wells.add(well)
        logger.info(f'Well has been added to the Project(pk={project.pk})')
    return cast(CustomWell, well)


def update_custom_well(well: CustomWell, user: User, **data: Any) -> CustomWell:
    logger.info(f'User(pk={user.pk}) is updating CustomWell(pk={well.pk})')

    for field_name, field_value in data.items():
        setattr(well, field_name, field_value)
    well.save()

    if not well.draft:
        sync_all_custom_well_co2_calculations_task.delay(well.pk)

    logger.info('Custom well has been updated')
    return well


def delete_custom_well(well: CustomWell, user: User) -> None:
    logger.info(f'User(pk={user.pk}) is deleting CustomWell(pk={well.pk})')
    plans = list(well.plans.all())
    well.delete()

    for plan in plans:
        sync_all_plan_co2_calculations_task.delay(plan.pk)
    logger.info('Well has been deleted')


def validate_well_planner_step_data(  # noqa: C901
    *,
    well_planner: WellPlanner,
    phase: CustomPhase,
    mode: CustomMode,
    season: AssetSeason,
    emission_reduction_initiatives: list[EmissionReductionInitiative] | None = None,
    materials: list[WellPlannerStepMaterialData] | None = None,
) -> None:
    emission_reduction_initiatives = [] if emission_reduction_initiatives is None else emission_reduction_initiatives
    materials = [] if materials is None else materials

    logger.info("Validating WellPlannerStepData.")

    if not BaselineInput.objects.filter(baseline=well_planner.baseline, phase=phase, mode=mode, season=season).exists():
        logger.info(
            f"WellPlannerStepData is not valid. BaselineInput(phase={phase.name}, mode={mode.name}, season={season}) "
            f"does not exist in Baseline(pk={well_planner.baseline_id})."
        )
        raise ValidationError("Invalid combination of phase, mode and season used.")

    for emission_reduction_initiative in emission_reduction_initiatives:
        if emission_reduction_initiative.emission_management_plan_id != well_planner.emission_management_plan_id:
            logger.info(
                f"WellPlannerStep data invalid. EmissionReductionInitiative(pk={emission_reduction_initiative.pk}) does not belong to EmissionManagementPlan(pk={well_planner.emission_management_plan_id})."
            )
            raise ValidationError(
                {"emission_reduction_initiatives": "Chosen energy reduction initiative is not a valid choice."}
            )
        if emission_reduction_initiative.deleted:
            logger.info(
                f"WellPlannerStep data invalid. EmissionReductionInitiative(pk={emission_reduction_initiative.pk}) is deleted."
            )
            raise ValidationError(
                {"emission_reduction_initiatives": "Chosen energy reduction initiative is not a valid choice."}
            )
        if emission_reduction_initiative.deployment_date > well_planner.planned_start_date:
            logger.info(
                f"WellPlannerStep data invalid. EmpInitiative(pk={emission_reduction_initiative.pk}) is not deployed yet."
            )
            raise ValidationError(
                {
                    "emission_reduction_initiatives": f"Energy reduction initiative \"{emission_reduction_initiative.name}\" is not deployed yet."
                }
            )

    for material_data in materials:
        material_type = material_data['material_type']

        if material_type.tenant_id != well_planner.asset.tenant_id:
            logger.info(
                f"WellPlannerStep data invalid. MaterialType(pk={material_type.pk}) does not belong to Tenant(pk={well_planner.asset.tenant_id})."
            )
            raise ValidationError({"materials": "Chosen material types are not  valid choices."})

        if material_type.deleted:
            logger.info(f"WellPlannerStep data invalid. MaterialType(pk={material_type.pk}) is deleted.")
            raise ValidationError({"materials": "Chosen material types are not  valid choices."})

    logger.info("WellPlannerStep data is valid.")


@transaction.atomic
@require_well_step(allowed_steps=[WellPlannerWizardStep.WELL_PLANNING], error='Phase cannot be created right now.')
def create_well_planner_planned_step(
    *,
    well_planner: WellPlanner,
    user: User,
    phase: CustomPhase,
    duration: float,
    waiting_on_weather: float,
    mode: CustomMode,
    season: AssetSeason,
    well_section_length: float,
    emission_reduction_initiatives: list[EmissionReductionInitiative],
    materials: list[WellPlannerStepMaterialData],
    comment: str,
    external_energy_supply_enabled: bool,
    external_energy_supply_quota: bool,
    carbon_capture_storage_system_quantity: float | None = None,
) -> WellPlannerPlannedStep:
    logger.info(
        f"User(pk={user.pk}) is creating WellPlannerPlannedStep(phase={phase}, mode={mode}) in WellPlanner(pk={well_planner.pk})."
    )
    validate_well_planner_step_data(
        well_planner=well_planner,
        phase=phase,
        mode=mode,
        season=season,
        emission_reduction_initiatives=emission_reduction_initiatives,
        materials=materials,
    )

    planned_step = WellPlannerPlannedStep.objects.create(
        well_planner=well_planner,
        duration=duration,
        waiting_on_weather=waiting_on_weather,
        phase=phase,
        mode=mode,
        season=season,
        carbon_capture_storage_system_quantity=carbon_capture_storage_system_quantity,
        improved_duration=duration,
        well_section_length=well_section_length,
        comment=comment,
        external_energy_supply_enabled=external_energy_supply_enabled,
        external_energy_supply_quota=external_energy_supply_quota,
    )
    planned_step.emission_reduction_initiatives.add(*emission_reduction_initiatives)
    planned_step.improved_duration = calculate_planned_step_improved_duration(planned_step)
    planned_step.save()

    set_well_step_materials(well_step=planned_step, materials=materials)

    logger.info(f"WellPlannerPlannedStep(pk={planned_step.pk}) has been created.")

    calculate_planned_emissions(well_planner)

    return cast(WellPlannerPlannedStep, planned_step)


@transaction.atomic
@require_well_step(
    allowed_steps=[WellPlannerWizardStep.WELL_PLANNING],
    error='Phase cannot be updated right now.',
    get_well=lambda *args, **kwargs: kwargs['planned_step'].well_planner,
)
def update_well_planner_planned_step(
    *,
    planned_step: WellPlannerPlannedStep,
    user: User,
    phase: CustomPhase,
    duration: float,
    waiting_on_weather: float,
    mode: CustomMode,
    season: AssetSeason,
    well_section_length: float,
    emission_reduction_initiatives: list[EmissionReductionInitiative],
    materials: list[WellPlannerStepMaterialData],
    comment: str,
    external_energy_supply_enabled: bool,
    external_energy_supply_quota: bool,
    carbon_capture_storage_system_quantity: float | None = None,
) -> WellPlannerPlannedStep:
    logger.info(f"User(pk={user.pk}) is updating WellPlannerPlannedStep(pk={planned_step.pk}).")

    validate_well_planner_step_data(
        well_planner=planned_step.well_planner,
        phase=phase,
        mode=mode,
        season=season,
        emission_reduction_initiatives=emission_reduction_initiatives,
        materials=materials,
    )

    planned_step.phase = phase
    planned_step.duration = duration
    planned_step.waiting_on_weather = waiting_on_weather
    planned_step.mode = mode
    planned_step.season = season
    planned_step.carbon_capture_storage_system_quantity = carbon_capture_storage_system_quantity
    planned_step.well_section_length = well_section_length
    planned_step.comment = comment
    planned_step.external_energy_supply_enabled = external_energy_supply_enabled
    planned_step.external_energy_supply_quota = external_energy_supply_quota
    planned_step.save()

    planned_step.emission_reduction_initiatives.set(emission_reduction_initiatives)

    planned_step.improved_duration = calculate_planned_step_improved_duration(planned_step)
    planned_step.save()

    set_well_step_materials(well_step=planned_step, materials=materials)

    logger.info(f"WellPlannerPlannedStep(pk={planned_step.pk}) has been updated.")

    calculate_planned_emissions(planned_step.well_planner)

    return planned_step


@transaction.atomic
@require_well_step(
    allowed_steps=[WellPlannerWizardStep.WELL_PLANNING],
    get_well=lambda *args, **kwargs: kwargs['planned_step'].well_planner,
    error='Phase cannot be deleted right now.',
)
def delete_well_planner_planned_step(*, planned_step: WellPlannerPlannedStep, user: User) -> None:
    logger.info(f"User(pk={user.pk}) is deleting WellPlannerPlannedStep(pk={planned_step.pk}).")
    well_plan = planned_step.well_planner

    planned_step.delete()

    logger.info(f"WellPlannerPlannedStep(pk={planned_step.pk}) has been deleted.")

    calculate_planned_emissions(well_plan)


WellPlannerStepType = TypeVar('WellPlannerStepType', bound=BaseWellPlannerStep)


def copy_well_planner_step(
    *, well_planner_step_class: type[WellPlannerStepType], copy_step: BaseWellPlannerStep, **extra_fields: Any
) -> WellPlannerStepType:
    duplicate_step = well_planner_step_class.objects.create(
        phase=copy_step.phase,
        mode=copy_step.mode,
        season=copy_step.season,
        carbon_capture_storage_system_quantity=copy_step.carbon_capture_storage_system_quantity,
        well_section_length=copy_step.well_section_length,
        comment=copy_step.comment,
        waiting_on_weather=copy_step.waiting_on_weather,
        external_energy_supply_enabled=copy_step.external_energy_supply_enabled,
        external_energy_supply_quota=copy_step.external_energy_supply_quota,
        **extra_fields,
    )

    duplicate_step.emission_reduction_initiatives.add(*copy_step.emission_reduction_initiatives.filter(deleted=False))

    for material in copy_step.materials.all():
        duplicate_step.materials.create(
            material_type=material.material_type,
            quantity=material.quantity,
            quota=material.quota,
        )

    return cast(WellPlannerStepType, duplicate_step)


@transaction.atomic
@require_well_step(allowed_steps=[WellPlannerWizardStep.WELL_PLANNING], error='Plan cannot be completed right now.')
def complete_well_planner_planning(*, well_planner: WellPlanner, user: User) -> WellPlanner:
    logger.info(
        f"User(pk={user.pk}) is completing WellPlanner(pk={well_planner.pk}) planning.",
    )
    if not well_planner.planned_steps.exists():  # type: ignore
        logger.info(f"Unable to complete WellPlanner(pk={well_planner.pk}). No steps added.")
        raise ValidationError("At least one phase must be added to complete the plan.")

    for well_planner_step in well_planner.planned_steps.order_by('order'):  # type: ignore
        copy_well_planner_step(
            well_planner_step_class=WellPlannerCompleteStep,
            copy_step=well_planner_step,
            well_planner=well_planner,
            duration=well_planner_step.improved_duration,
            approved=False,
        )

    for planned_helicopter_use in well_planner.plannedhelicopteruse_set.order_by('id'):
        CompleteHelicopterUse.objects.create(
            well_planner=well_planner,
            helicopter_type=planned_helicopter_use.helicopter_type,
            trips=planned_helicopter_use.trips,
            trip_duration=planned_helicopter_use.trip_duration,
            exposure_against_current_well=planned_helicopter_use.exposure_against_current_well,
            quota_obligation=planned_helicopter_use.quota_obligation,
            approved=False,
        )

    for planned_vessel_use in well_planner.plannedvesseluse_set.order_by('id'):
        CompleteVesselUse.objects.create(
            well_planner=well_planner,
            vessel_type=planned_vessel_use.vessel_type,
            season=planned_vessel_use.season,
            duration=planned_vessel_use.duration,
            exposure_against_current_well=planned_vessel_use.exposure_against_current_well,
            waiting_on_weather=planned_vessel_use.waiting_on_weather,
            quota_obligation=planned_vessel_use.quota_obligation,
            approved=False,
        )

    well_planner.current_step = WellPlannerWizardStep.WELL_REVIEWING
    well_planner.actual_start_date = well_planner.planned_start_date
    well_planner.save()
    logger.info(f"WellPlanner(pk={well_planner.pk}) planning has been completed.")
    return well_planner


def split_duration_into_days(
    *, start_date: datetime.datetime, total_days: float, duration: float
) -> Generator[tuple[datetime.datetime, float], None, None]:
    while duration > 0:
        time_left_in_day = int(total_days) + 1 - total_days
        current_date = start_date + datetime.timedelta(days=total_days)
        if duration <= time_left_in_day:
            yield current_date, duration
            duration = 0
        else:
            yield current_date, time_left_in_day
            duration -= time_left_in_day
            total_days += time_left_in_day


class DurationHoursResult(TypedDict):
    hour: datetime.datetime
    duration: float
    start: datetime.datetime
    end: datetime.datetime


def split_duration_into_hours(
    *, start_date: datetime.datetime, duration: float
) -> Generator[DurationHoursResult, None, None]:
    if duration > 1:
        raise ValueError('Duration cannot be greater than 1')
    end_date = start_date + datetime.timedelta(days=duration)
    while True:
        current_hour = start_date.replace(minute=0, second=0, microsecond=0)
        next_hour = current_hour + datetime.timedelta(hours=1)
        if start_date.date() == end_date.date() and start_date.hour == end_date.hour:
            yield DurationHoursResult(
                hour=current_hour, duration=(end_date.minute - start_date.minute) / 60, start=start_date, end=end_date
            )
        else:
            yield DurationHoursResult(
                hour=current_hour, duration=(60 - start_date.minute) / 60, start=start_date, end=next_hour
            )

        start_date = next_hour

        if next_hour >= end_date:
            break


def get_well_planner_hourly_co2_dataset(
    *,
    start_date: datetime.datetime,
    end_date: datetime.datetime,
    step_co2: WellPlannerStepCO2Result,
    step_duration: float,
    step_waiting_duration: float,
    plan_start_date: datetime.datetime,
) -> list[WellPlannerCo2Dataset]:
    dataset: list[WellPlannerCo2Dataset] = []
    step_start_date = plan_start_date + datetime.timedelta(days=step_waiting_duration)
    step_end_date = step_start_date + datetime.timedelta(days=step_duration)

    if step_end_date < start_date or step_start_date > end_date:
        return dataset

    hourly_co2 = multiply_well_planner_step_co2(step_co2, 1 / (step_duration * 24))

    for day_date, day_duration in split_duration_into_days(
        start_date=plan_start_date, total_days=step_waiting_duration, duration=step_duration
    ):
        for result in split_duration_into_hours(start_date=day_date, duration=day_duration):
            if not (start_date <= result['hour'] <= end_date):
                continue

            co2_data = multiply_well_planner_step_co2(hourly_co2, result['duration'])
            entry = WellPlannerCo2Dataset(
                date=result['hour'],
                **co2_data,  # type: ignore
            )
            dataset.append(entry)
    return dataset


def get_well_planner_daily_co2_dataset(
    *,
    step_co2: WellPlannerStepCO2Result,
    step_duration: float,
    step_waiting_duration: float,
    plan_start_date: datetime.datetime,
) -> list[WellPlannerCo2Dataset]:
    daily_co2 = multiply_well_planner_step_co2(step_co2, 1 / step_duration)
    dataset: list[WellPlannerCo2Dataset] = []

    for day_date, day_duration in split_duration_into_days(
        start_date=plan_start_date, total_days=step_waiting_duration, duration=step_duration
    ):
        co2_data = multiply_well_planner_step_co2(daily_co2, day_duration)
        entry = WellPlannerCo2Dataset(
            date=datetime.datetime.combine(day_date, datetime.datetime.min.time()),
            **co2_data,  # type: ignore
        )
        dataset.append(entry)

    return dataset


def get_well_planner_planned_co2_dataset(
    *,
    well_planner: WellPlanner,
    improved: bool,
    start_date: datetime.datetime | None = None,
    end_date: datetime.datetime | None = None,
) -> list[WellPlannerStepCo2Dataset]:
    def get_step_duration(step: WellPlannerPlannedStep) -> float:
        if improved:
            return step.improved_duration
        return step.total_duration

    logger.info(f"Generating well planner planned CO2 dataset for WellPlanner(pk={well_planner.pk}).")
    well_planner_planned_steps = well_planner.planned_steps.order_by('order')  # type: ignore

    total_well_planner_duration = sum(get_step_duration(step) for step in well_planner_planned_steps)

    dataset: list[WellPlannerStepCo2Dataset] = []
    plan_start_date = datetime.datetime(
        day=well_planner.planned_start_date.day,
        month=well_planner.planned_start_date.month,
        year=well_planner.planned_start_date.year,
        tzinfo=pytz.UTC,
    )
    processed_duration = 0.0
    seasons_duration = get_seasons_duration(
        [(get_step_duration(step), step.season) for step in well_planner_planned_steps]
    )

    for planned_step in well_planner_planned_steps:
        logger.info(f"Processing WellPlannerPlannedStep(pk={planned_step.pk}).")

        step_duration = get_step_duration(planned_step)

        well_planner_step_co2 = calculate_well_planner_step_co2(
            planned_step=planned_step,
            duration=step_duration,
            total_duration=total_well_planner_duration,
            total_season_duration=seasons_duration[planned_step.season],
        )

        if start_date and end_date:
            dataset.extend(
                map(
                    lambda data: WellPlannerStepCo2Dataset(**data, step=planned_step),  # type: ignore
                    get_well_planner_hourly_co2_dataset(
                        start_date=start_date,
                        end_date=end_date,
                        plan_start_date=plan_start_date,
                        step_co2=well_planner_step_co2,
                        step_duration=step_duration,
                        step_waiting_duration=processed_duration,
                    ),
                )
            )
        else:
            dataset.extend(
                map(
                    lambda data: WellPlannerStepCo2Dataset(**data, step=planned_step),  # type: ignore
                    get_well_planner_daily_co2_dataset(
                        plan_start_date=plan_start_date,
                        step_co2=well_planner_step_co2,
                        step_duration=step_duration,
                        step_waiting_duration=processed_duration,
                    ),
                )
            )

        processed_duration += step_duration

    logger.info(f"Well planner dataset for WellPlanner(pk={well_planner.pk}) has been generated.")
    return dataset


def get_well_planner_planned_duration(well_planner: WellPlanner) -> tuple[float, float]:
    planned_steps = well_planner.planned_steps.order_by('order')  # type: ignore
    total_duration = sum(step.total_duration for step in planned_steps)
    total_improved_duration = sum(step.improved_duration for step in planned_steps)

    return total_duration, total_improved_duration


def get_well_planner_saved_co2_dataset(
    *, well_planner: WellPlanner, start_date: datetime.datetime | None = None, end_date: datetime.datetime | None = None
) -> list[WellPlannerCo2Dataset]:
    total_planned_duration, total_improved_duration = get_well_planner_planned_duration(well_planner)
    saved_duration = total_planned_duration - total_improved_duration

    if saved_duration <= 0:
        return []

    plan_start_date = datetime.datetime(
        day=well_planner.planned_start_date.day,
        month=well_planner.planned_start_date.month,
        year=well_planner.planned_start_date.year,
        tzinfo=pytz.UTC,
    )
    saved_co2 = calculate_well_planner_co2_improvement(well_planner)

    if start_date and end_date:
        return get_well_planner_hourly_co2_dataset(
            start_date=start_date,
            end_date=end_date,
            step_co2=saved_co2,
            step_duration=saved_duration,
            step_waiting_duration=total_improved_duration,
            plan_start_date=plan_start_date,
        )
    else:
        return get_well_planner_daily_co2_dataset(
            step_co2=saved_co2,
            step_duration=saved_duration,
            plan_start_date=plan_start_date,
            step_waiting_duration=total_improved_duration,
        )


def get_well_planner_summary(well_planner: WellPlanner) -> WellPlannerSummary:
    _, total_improved_duration = get_well_planner_planned_duration(well_planner)
    well_planner_summary = WellPlannerSummary(
        total_baseline=0.0,
        total_target=0.0,
        total_improved_duration=total_improved_duration,
    )
    well_planner_planned_steps = well_planner.planned_steps.order_by('order')  # type: ignore
    seasons_duration = get_seasons_duration(
        [(step.improved_duration, step.season) for step in well_planner_planned_steps]
    )

    for planned_step in well_planner_planned_steps:
        improved_well_planner_step_co2 = calculate_well_planner_step_co2(
            planned_step=planned_step,
            duration=planned_step.improved_duration,
            total_duration=total_improved_duration,
            total_season_duration=seasons_duration[planned_step.season],
        )

        well_planner_summary['total_baseline'] += improved_well_planner_step_co2['baseline']
        well_planner_summary['total_target'] += improved_well_planner_step_co2['target']

    return well_planner_summary


def set_well_planner_to_review(well_planner: WellPlanner) -> WellPlanner:
    logger.info("Setting WellPlanner(pk={well_planner.pk}) current step to reviewing.")
    well_planner.current_step = WellPlannerWizardStep.WELL_REVIEWING
    well_planner.save()
    logger.info(f"WellPlanner(pk={well_planner.pk}) current step has been set to reviewing.")
    return well_planner


@transaction.atomic
@require_well_step(
    allowed_steps=[WellPlannerWizardStep.WELL_REVIEWING, WellPlannerWizardStep.WELL_REPORTING],
    error='Phase cannot be created right now.',
)
def create_well_planner_complete_step(
    *,
    well_planner: WellPlanner,
    user: User,
    phase: CustomPhase,
    duration: float,
    waiting_on_weather: float,
    season: AssetSeason,
    mode: CustomMode,
    well_section_length: float,
    emission_reduction_initiatives: list[EmissionReductionInitiative],
    materials: list[WellPlannerStepMaterialData],
    external_energy_supply_enabled: bool,
    external_energy_supply_quota: bool,
    comment: str | None = None,
    carbon_capture_storage_system_quantity: float | None = None,
) -> WellPlannerCompleteStep:
    logger.info(
        f"User(pk={user.pk}) is creating WellPlannerCompleteStep(phase={phase}, mode={mode}) in WellPlanner(pk={well_planner.pk})."
    )
    validate_well_planner_step_data(
        well_planner=well_planner,
        phase=phase,
        mode=mode,
        season=season,
        emission_reduction_initiatives=emission_reduction_initiatives,
        materials=materials,
    )

    complete_step = WellPlannerCompleteStep.objects.create(
        well_planner=well_planner,
        phase=phase,
        waiting_on_weather=waiting_on_weather,
        duration=duration,
        season=season,
        mode=mode,
        well_section_length=well_section_length,
        approved=False,
        carbon_capture_storage_system_quantity=carbon_capture_storage_system_quantity,
        external_energy_supply_enabled=external_energy_supply_enabled,
        external_energy_supply_quota=external_energy_supply_quota,
        comment=comment or "",
    )
    complete_step.emission_reduction_initiatives.add(*emission_reduction_initiatives)

    set_well_step_materials(well_step=complete_step, materials=materials)
    set_well_planner_to_review(well_planner)

    logger.info(f"WellPlannerCompleteStep(pk={complete_step.pk}) has been created.")
    return cast(WellPlannerCompleteStep, complete_step)


@transaction.atomic
@require_well_step(
    allowed_steps=[WellPlannerWizardStep.WELL_REVIEWING, WellPlannerWizardStep.WELL_REPORTING],
    get_well=lambda *args, **kwargs: kwargs['complete_step'].well_planner,
    error='Phase cannot be updated right now.',
)
def update_well_planner_complete_step(
    *,
    complete_step: WellPlannerCompleteStep,
    user: User,
    phase: CustomPhase,
    duration: float,
    mode: CustomMode,
    season: AssetSeason,
    well_section_length: float,
    emission_reduction_initiatives: list[EmissionReductionInitiative],
    materials: list[WellPlannerStepMaterialData],
    waiting_on_weather: float,
    external_energy_supply_enabled: bool,
    external_energy_supply_quota: bool,
    comment: str | None = None,
    carbon_capture_storage_system_quantity: float | None = None,
) -> WellPlannerCompleteStep:
    logger.info(f"User(pk={user.pk}) is updating WellPlannerCompleteStep(pk={complete_step.pk}).")

    validate_well_planner_step_data(
        well_planner=complete_step.well_planner,
        phase=phase,
        mode=mode,
        season=season,
        emission_reduction_initiatives=emission_reduction_initiatives,
        materials=materials,
    )

    complete_step.phase = phase
    complete_step.duration = duration
    complete_step.mode = mode
    complete_step.season = season
    complete_step.well_section_length = well_section_length
    complete_step.waiting_on_weather = waiting_on_weather
    complete_step.external_energy_supply_enabled = external_energy_supply_enabled
    complete_step.external_energy_supply_quota = external_energy_supply_quota
    complete_step.carbon_capture_storage_system_quantity = carbon_capture_storage_system_quantity
    complete_step.comment = comment or ""
    complete_step.approved = False
    complete_step.save()

    complete_step.emission_reduction_initiatives.set(emission_reduction_initiatives)

    set_well_step_materials(well_step=complete_step, materials=materials)
    set_well_planner_to_review(complete_step.well_planner)

    logger.info(f"WellPlannerCompleteStep(pk={complete_step.pk}) has been updated.")
    return complete_step


@transaction.atomic
@require_well_step(
    allowed_steps=[WellPlannerWizardStep.WELL_REVIEWING, WellPlannerWizardStep.WELL_REPORTING],
    get_well=lambda *args, **kwargs: kwargs['complete_step'].well_planner,
    error='Phase cannot be deleted right now.',
)
def delete_well_planner_complete_step(*, complete_step: WellPlannerCompleteStep, user: User) -> None:
    logger.info(f"User(pk={user.pk}) is deleting WellPlannerCompleteStep(pk={complete_step.pk}).")

    set_well_planner_to_review(complete_step.well_planner)
    complete_step.delete()

    logger.info(f"WellPlannerCompleteStep(pk={complete_step.pk}) has been deleted.")


@transaction.atomic
@require_well_step(
    allowed_steps=[WellPlannerWizardStep.WELL_REVIEWING, WellPlannerWizardStep.WELL_REPORTING],
    error='Plan cannot be completed right now.',
)
def complete_well_planner_reviewing(*, well_planner: WellPlanner, user: User) -> WellPlanner:
    logger.info(f"User(pk={user.pk}) is completing WellPlanner(pk={well_planner.pk}) reviewing.")

    if well_planner.current_step not in [WellPlannerWizardStep.WELL_REVIEWING, WellPlannerWizardStep.WELL_REPORTING]:
        logger.info(
            f"Unable to complete WellPlanner(pk={well_planner.pk}). Current step must be '{WellPlannerWizardStep.WELL_REVIEWING}'."
        )
        raise ValidationError("Plan cannot be completed right now.")

    if not well_planner.complete_steps.exists():  # type: ignore
        raise ValidationError("At least one phase must be added to complete the plan.")

    if well_planner.complete_steps.filter(approved=False).exists():  # type: ignore
        raise ValidationError("All phases must be approved to complete the review.")

    if well_planner.completehelicopteruse_set.filter(approved=False).exists():
        raise ValidationError("All helicopters must be approved to complete the review.")

    if well_planner.completevesseluse_set.filter(approved=False).exists():
        raise ValidationError("All vessels must be approved to complete the review.")

    well_planner.current_step = WellPlannerWizardStep.WELL_REPORTING
    well_planner.save()

    logger.info(f"WellPlanner(pk={well_planner.pk}) reviewing has been completed.")
    return well_planner


@transaction.atomic
@require_well_step(
    allowed_steps=[WellPlannerWizardStep.WELL_REVIEWING, WellPlannerWizardStep.WELL_REPORTING],
    error='Phases cannot be approved right now.',
)
def approve_well_planner_complete_steps(
    *, well_planner: WellPlanner, user: User, complete_steps: list[WellPlannerCompleteStep]
) -> None:
    logger.info(f"User(pk={user.pk}) is approving complete steps in WellPlanner(pk={well_planner.pk}).")

    for complete_step in complete_steps:
        if complete_step.well_planner_id != well_planner.pk:
            logger.info(
                f"Unable approve WellPlannerCompleteStep(pk={complete_step.pk}). "
                f"Expected WellPlanner(pk={well_planner.pk}) but "
                f"received WellPlanner(pk={complete_step.well_planner_id})."
            )
            raise ValidationError({"steps": f'Phase "{complete_step.pk}" doesn\'t exist.'})

        complete_step.approved = True
        complete_step.save()

        logger.info(f"WellPlannerCompleteStep(pk={complete_step.pk}) has been approved.")

    logger.info(f'Approved {len(complete_steps)} complete steps')


def get_well_planner_daily_measured_co2_dataset(
    *,
    complete_step: WellPlannerCompleteStep,
    plan_start_date: datetime.datetime,
    plan_duration: float,
    season_duration: float,
    step_waiting_duration: float,
    step_duration: float,
) -> list[WellPlannerStepCo2Dataset]:
    dataset = []
    for day_date, day_duration in split_duration_into_days(
        start_date=plan_start_date, total_days=step_waiting_duration, duration=step_duration
    ):
        day_start = day_date
        day_end = day_start + datetime.timedelta(days=day_duration)

        co2_data = calculate_measured_well_planner_step_co2(
            complete_step=complete_step,
            start=day_start,
            end=day_end,
            total_duration=plan_duration,
            total_season_duration=season_duration,
        )
        entry = WellPlannerStepCo2Dataset(
            date=datetime.datetime.combine(day_date, datetime.datetime.min.time()),
            step=complete_step,
            **co2_data,  # type: ignore
        )
        dataset.append(entry)
    return dataset


def get_well_planner_hourly_measured_co2_dataset(
    *,
    start_date: datetime.datetime,
    end_date: datetime.datetime,
    complete_step: WellPlannerCompleteStep,
    plan_start_date: datetime.datetime,
    plan_duration: float,
    season_duration: float,
    step_waiting_duration: float,
    step_duration: float,
) -> list[WellPlannerStepCo2Dataset]:
    dataset: list[WellPlannerStepCo2Dataset] = []
    step_start_date = plan_start_date + datetime.timedelta(days=step_waiting_duration)
    step_end_date = step_start_date + datetime.timedelta(days=step_duration)

    if step_end_date < start_date or step_start_date > end_date:
        return dataset

    for day_date, day_duration in split_duration_into_days(
        start_date=plan_start_date, total_days=step_waiting_duration, duration=step_duration
    ):
        for result in split_duration_into_hours(start_date=day_date, duration=day_duration):
            if not (start_date <= result['hour'] <= end_date):
                continue

            co2_data = calculate_measured_well_planner_step_co2(
                complete_step=complete_step,
                start=result['start'],
                end=result['end'],
                total_duration=plan_duration,
                total_season_duration=season_duration,
            )
            entry = WellPlannerStepCo2Dataset(
                date=result['hour'],
                step=complete_step,
                **co2_data,  # type: ignore
            )
            dataset.append(entry)

    return dataset


def get_well_planner_measured_co2_dataset(
    *, well_planner: WellPlanner, start_date: datetime.datetime | None = None, end_date: datetime.datetime | None = None
) -> list[WellPlannerStepCo2Dataset]:
    logger.info(f"Generating well planner measured dataset for WellPlanner(pk={well_planner.pk}).")

    assert well_planner.actual_start_date, f"WellPlanner(pk={well_planner.pk}) is missing actual start date"

    well_planner_complete_steps = well_planner.complete_steps.order_by('order')  # type: ignore
    plan_duration = sum(complete_step.duration for complete_step in well_planner_complete_steps)
    seasons_duration = get_seasons_duration(
        [(complete_step.duration, complete_step.season) for complete_step in well_planner_complete_steps]
    )

    dataset: list[WellPlannerStepCo2Dataset] = []
    plan_start_date = datetime.datetime(
        day=well_planner.actual_start_date.day,
        month=well_planner.actual_start_date.month,
        year=well_planner.actual_start_date.year,
        tzinfo=pytz.UTC,
    )
    processed_duration = 0

    for complete_step in well_planner_complete_steps:
        logger.info(f"Processing WellPlannerCompleteStep(pk={complete_step.pk}).")
        step_duration = complete_step.duration

        if start_date and end_date:
            dataset.extend(
                get_well_planner_hourly_measured_co2_dataset(
                    start_date=start_date,
                    end_date=end_date,
                    complete_step=complete_step,
                    plan_start_date=plan_start_date,
                    plan_duration=plan_duration,
                    season_duration=seasons_duration[complete_step.season],
                    step_waiting_duration=processed_duration,
                    step_duration=step_duration,
                )
            )
        else:
            dataset.extend(
                get_well_planner_daily_measured_co2_dataset(
                    complete_step=complete_step,
                    plan_start_date=plan_start_date,
                    plan_duration=plan_duration,
                    season_duration=seasons_duration[complete_step.season],
                    step_waiting_duration=processed_duration,
                    step_duration=step_duration,
                )
            )
        processed_duration += step_duration

    logger.info(f"Well planner measured dataset for WellPlanner(pk={well_planner.pk}) has been generated.")
    return dataset


def get_well_planner_measurement_daily_dataset(
    *,
    plan_start_date: datetime.datetime,
    plan_end_date: datetime.datetime,
    monitor_function_type: MonitorFunctionType,
    vessel_id: int,
) -> QuerySet:
    monitor_function_values = (
        MonitorFunctionValue.objects.filter(
            monitor_function__vessel__pk=vessel_id,
            monitor_function__type=monitor_function_type,
            monitor_function__draft=False,
            date__date=OuterRef('term'),
        )
        .values('date__date')
        .annotate(average=Coalesce(Avg('value'), 0, output_field=FloatField()))
    )
    return cast(
        QuerySet,
        (
            generate_series(plan_start_date, plan_end_date, "1 days", output_field=DateTimeField)
            .annotate(date=F('term'))
            .annotate(value=Subquery(monitor_function_values.values('average')[:1]))
        ),
    )


def get_well_planner_measurement_hourly_dataset(
    *,
    start_date: datetime.datetime,
    end_date: datetime.datetime,
    plan_start_date: datetime.datetime,
    plan_end_date: datetime.datetime,
    monitor_function_type: MonitorFunctionType,
    vessel_id: int,
) -> QuerySet:
    monitor_function_values = MonitorFunctionValue.objects.filter(
        monitor_function__vessel__pk=vessel_id,
        monitor_function__type=monitor_function_type,
        monitor_function__draft=False,
        date=OuterRef('term'),
    )
    return cast(
        QuerySet,
        (
            generate_series(plan_start_date, plan_end_date, "1 hour", output_field=DateTimeField)
            .annotate(date=F('term'))
            .annotate(
                value=Coalesce(Subquery(monitor_function_values.values('value')[:1]), 0, output_field=FloatField())
            )
            .filter(date__gte=start_date, date__lte=end_date)
        ),
    )


def get_well_planner_measurement_dataset(
    *,
    well_planner: WellPlanner,
    monitor_function_type: MonitorFunctionType,
    start_date: datetime.datetime | None = None,
    end_date: datetime.datetime | None = None,
) -> list[WellPlannerMeasurementDataset]:
    logger.info(
        f"Generating well planner '{monitor_function_type}' measurement dataset for WellPlanner(pk={well_planner.pk})."
    )

    assert well_planner.actual_start_date, f"WellPlanner(pk={well_planner.pk}) is missing actual start date"

    if not well_planner.asset.vessel_id:
        logger.info(f"WellPlanner(pk={well_planner.pk}) has no vessel assigned. Returning empty dataset.")
        return []

    total_duration = sum(complete_step.duration for complete_step in well_planner.complete_steps.all())  # type: ignore
    plan_start_date = datetime.datetime(
        year=well_planner.actual_start_date.year,
        month=well_planner.actual_start_date.month,
        day=well_planner.actual_start_date.day,
        tzinfo=pytz.UTC,
    )

    if start_date and end_date:
        plan_end_date = plan_start_date + datetime.timedelta(days=total_duration)
        queryset = get_well_planner_measurement_hourly_dataset(
            start_date=start_date,
            end_date=end_date,
            plan_start_date=plan_start_date,
            plan_end_date=plan_end_date,
            monitor_function_type=monitor_function_type,
            vessel_id=int(well_planner.asset.vessel_id),
        )
    else:
        if int(total_duration) == total_duration and total_duration:
            plan_end_date = plan_start_date + datetime.timedelta(days=total_duration - 1)
        else:
            plan_end_date = plan_start_date + datetime.timedelta(days=total_duration)

        queryset = get_well_planner_measurement_daily_dataset(
            plan_start_date=plan_start_date,
            plan_end_date=plan_end_date,
            monitor_function_type=monitor_function_type,
            vessel_id=int(well_planner.asset.vessel_id),
        )
    logger.info(
        f"Well planner '{monitor_function_type}' measurement dataset for WellPlanner(pk={well_planner.pk}) has been generated."
    )
    return [WellPlannerMeasurementDataset(date=item.date, value=item.value) for item in queryset]


def get_well_planner_measured_summary(well_planner: WellPlanner) -> WellPlannerMeasuredSummary:
    assert well_planner.actual_start_date, f"WellPlanner(pk={well_planner.pk}) is missing actual start date"

    complete_steps = well_planner.complete_steps.order_by('order')  # type: ignore
    total_measured_duration = sum(complete_step.duration for complete_step in complete_steps)
    seasons_duration = get_seasons_duration(
        [(complete_step.duration, complete_step.season) for complete_step in complete_steps]
    )
    well_planner_measured_summary = WellPlannerMeasuredSummary(
        total_baseline=0.0,
        total_target=0.0,
        total_duration=total_measured_duration,
    )

    current_datetime = datetime.datetime(
        year=well_planner.actual_start_date.year,
        month=well_planner.actual_start_date.month,
        day=well_planner.actual_start_date.day,
    )

    for complete_step in well_planner.complete_steps.order_by('order'):  # type: ignore
        measured_well_planner_step_co2 = calculate_measured_well_planner_step_co2(
            complete_step=complete_step,
            start=current_datetime,
            end=current_datetime + datetime.timedelta(days=complete_step.duration),
            total_duration=total_measured_duration,
            total_season_duration=seasons_duration[complete_step.season],
        )
        well_planner_measured_summary['total_baseline'] += measured_well_planner_step_co2['baseline']
        well_planner_measured_summary['total_target'] += measured_well_planner_step_co2['target']

        current_datetime += datetime.timedelta(days=complete_step.duration)

    return well_planner_measured_summary


@transaction.atomic
@require_well_step(
    allowed_steps=[
        WellPlannerWizardStep.WELL_PLANNING,
    ],
    get_well=lambda *args, **kwargs: kwargs['planned_step'].well_planner,
    error='Step cannot be duplicated right now.',
)
def duplicate_well_planner_planned_step(*, planned_step: WellPlannerPlannedStep, user: User) -> WellPlannerPlannedStep:
    logger.info(f"User(pk={user.pk}) is duplicating WellPlannerPlannedStep(pk={planned_step.pk}).")
    if planned_step.well_planner.current_step != WellPlannerWizardStep.WELL_PLANNING:
        logger.error(
            f"Unable to duplicate WellPlannerPlannedStep(pk={planned_step.pk}). Current step must be "
            f"'{WellPlannerWizardStep.WELL_PLANNING}' but received '{planned_step.well_planner.current_step}'."
        )
        raise ValidationError("Step cannot be duplicate right now.")

    duplicate_step = copy_well_planner_step(
        well_planner_step_class=WellPlannerPlannedStep,
        copy_step=planned_step,
        well_planner=planned_step.well_planner,
        duration=planned_step.duration,
        improved_duration=planned_step.improved_duration,
    )
    duplicate_step.save()

    duplicate_step.below(planned_step)

    calculate_planned_emissions(planned_step.well_planner)

    return duplicate_step


@transaction.atomic
@require_well_step(
    allowed_steps=[
        WellPlannerWizardStep.WELL_REVIEWING,
        WellPlannerWizardStep.WELL_REPORTING,
    ],
    get_well=lambda *args, **kwargs: kwargs['complete_step'].well_planner,
    error='Step cannot be duplicated right now.',
)
def duplicate_well_planner_complete_step(
    *, complete_step: WellPlannerCompleteStep, user: User
) -> WellPlannerCompleteStep:
    logger.info(f"User(pk={user.pk}) is duplicating WellPlannerCompleteStep(pk={complete_step.pk}).")
    if complete_step.well_planner.current_step not in [
        WellPlannerWizardStep.WELL_REVIEWING,
        WellPlannerWizardStep.WELL_REPORTING,
    ]:
        logger.error(
            f"Unable to duplicate WellPlannerCompleteStep(pk={complete_step.pk}). Current step must be "
            f"'{WellPlannerWizardStep.WELL_REVIEWING}' or {WellPlannerWizardStep.WELL_REPORTING} but received "
            f"'{complete_step.well_planner.current_step}'."
        )
        raise ValidationError("Step cannot be duplicate right now.")

    duplicate_step = copy_well_planner_step(
        well_planner_step_class=WellPlannerCompleteStep,
        copy_step=complete_step,
        well_planner=complete_step.well_planner,
        duration=complete_step.duration,
        approved=False,
    )

    duplicate_step.below(complete_step)

    complete_step.well_planner.current_step = WellPlannerWizardStep.WELL_REVIEWING
    complete_step.well_planner.save()

    return duplicate_step


@transaction.atomic
@require_well_step(
    allowed_steps=[
        WellPlannerWizardStep.WELL_PLANNING,
    ],
    get_well=lambda *args, **kwargs: kwargs['step'].well_planner,
    error='Step cannot be moved right now.',
)
def move_well_planner_planned_step(*, user: User, step: WellPlannerPlannedStep, order: int) -> WellPlannerPlannedStep:
    well_plan = step.well_planner
    logger.info(
        f'User(pk={user.pk}) is moving WellPlannerPlannedStep(pk={step.pk}) to position {order} '
        f'in WellPlanner(pk={well_plan.pk})',
    )
    if well_plan.current_step != WellPlannerWizardStep.WELL_PLANNING:
        logger.error(
            f"Unable to move WellPlannerPlannedStep(pk={step.pk}) in WellPlanner(pk={well_plan.pk}). "
            f"Current step must be '{WellPlannerWizardStep.WELL_PLANNING}' but received '{well_plan.current_step}'."
        )
        raise ValidationError("Step cannot be moved right now.")

    step.to(order=order)

    logger.info('Moved step')

    calculate_planned_emissions(well_plan)

    return step


@transaction.atomic
@require_well_step(
    allowed_steps=[
        WellPlannerWizardStep.WELL_REVIEWING,
        WellPlannerWizardStep.WELL_REPORTING,
    ],
    get_well=lambda *args, **kwargs: kwargs['step'].well_planner,
    error='Step cannot be moved right now.',
)
def move_well_planner_complete_step(
    *, user: User, step: WellPlannerCompleteStep, order: int
) -> WellPlannerCompleteStep:
    well_planner = step.well_planner
    logger.info(
        f'User(pk={user.pk}) is moving WellPlannerCompleteStep(pk={step.pk}) to position {order} in WellPlanner(pk={well_planner.pk})',
    )
    if well_planner.current_step not in [WellPlannerWizardStep.WELL_REVIEWING, WellPlannerWizardStep.WELL_REPORTING]:
        logger.error(
            f"Unable to move WellPlannerCompleteStep(pk={step.pk}) in WellPlanner(pk={well_planner.pk}). "
            f"Current step must be '{WellPlannerWizardStep.WELL_REVIEWING}' but received '{well_planner.current_step}'."
        )
        raise ValidationError("Step cannot be moved right now.")

    step.to(order=order)

    step.approved = False
    step.save()

    well_planner.current_step = WellPlannerWizardStep.WELL_REVIEWING
    well_planner.save()

    return step


def get_well_planner_planned_step_co2(*, user: User, planned_step: WellPlannerPlannedStep) -> WellPlannerStepCO2Result:
    logger.info(f"User(pk={user.pk}) is calculating CO2 for WellPlannerPlannedStep(pk={planned_step.pk}).")

    _, total_improved_duration = get_well_planner_planned_duration(planned_step.well_planner)
    well_planner_planned_steps = planned_step.well_planner.planned_steps.order_by('order')  # type: ignore
    seasons_duration = get_seasons_duration(
        [(step.improved_duration, step.season) for step in well_planner_planned_steps]
    )

    well_planner_step_co2 = calculate_well_planner_step_co2(
        planned_step=planned_step,
        duration=planned_step.improved_duration,
        total_duration=total_improved_duration,
        total_season_duration=seasons_duration[cast(AssetSeason, planned_step.season)],
    )

    logger.info('Calculated CO2')

    return well_planner_step_co2


def set_complete_step_to_review(complete_step: WellPlannerCompleteStep) -> WellPlannerCompleteStep:
    logger.info(f"Setting WellPlannerCompleteStep(pk={complete_step.pk}) to reviewing.")

    set_well_planner_to_review(complete_step.well_planner)
    complete_step.approved = False
    complete_step.save()

    logger.info(f"WellPlannerCompleteStep(pk={complete_step.pk}) has been set to reviewing.")
    return complete_step


@require_well_step(
    allowed_steps=[
        WellPlannerWizardStep.WELL_PLANNING,
    ],
    get_well=lambda *args, **kwargs: kwargs['planned_step'].well_planner,
    error='Energy reduction initiatives cannot be updated right now.',
)
@transaction.atomic
def update_well_planner_planned_step_emission_reduction_initiatives(
    *,
    user: User,
    planned_step: WellPlannerPlannedStep,
    emission_reduction_initiatives: list[EmissionReductionInitiative],
) -> WellPlannerPlannedStep:
    logger.info(
        f"User(pk={user.pk}) is updating WellPlannerPlannedStep(pk={planned_step.pk})'s emission reduction initiatives."
    )

    validate_well_planner_step_data(
        well_planner=planned_step.well_planner,
        phase=planned_step.phase,
        mode=planned_step.mode,
        season=cast(AssetSeason, planned_step.season),
        emission_reduction_initiatives=emission_reduction_initiatives,
    )
    planned_step.emission_reduction_initiatives.set(emission_reduction_initiatives)
    planned_step.improved_duration = calculate_planned_step_improved_duration(planned_step)
    planned_step.save()

    logger.info(f"WellPlannerPlannedStep(pk={planned_step.pk})'s emission reduction initiatives have been updated.")

    calculate_planned_emissions(planned_step.well_planner)
    return planned_step


@transaction.atomic
@require_well_step(
    allowed_steps=[
        WellPlannerWizardStep.WELL_REVIEWING,
        WellPlannerWizardStep.WELL_REPORTING,
    ],
    get_well=lambda *args, **kwargs: kwargs['complete_step'].well_planner,
    error='Energy reduction initiatives cannot be updated right now.',
)
def update_well_planner_complete_step_emission_reduction_initiatives(
    *,
    user: User,
    complete_step: WellPlannerCompleteStep,
    emission_reduction_initiatives: list[EmissionReductionInitiative],
) -> WellPlannerCompleteStep:
    logger.info(
        f"User(pk={user.pk}) is updating WellPlannerCompleteStep(pk={complete_step.pk})'s emission reduction initiatives."
    )

    validate_well_planner_step_data(
        well_planner=complete_step.well_planner,
        phase=complete_step.phase,
        mode=complete_step.mode,
        season=cast(AssetSeason, complete_step.season),
        emission_reduction_initiatives=emission_reduction_initiatives,
    )
    complete_step.emission_reduction_initiatives.set(emission_reduction_initiatives)
    set_complete_step_to_review(complete_step=complete_step)

    logger.info(f"WellPlannerCompleteStep(pk={complete_step.pk})'s emission reduction initiatives have been updated.")
    return complete_step


@transaction.atomic
@require_well_step(
    allowed_steps=[
        WellPlannerWizardStep.WELL_REVIEWING,
        WellPlannerWizardStep.WELL_REPORTING,
    ],
    error='Helicopter use cannot be approved right now.',
)
def approve_well_planner_complete_helicopter_uses(
    *, user: User, well_planner: WellPlanner, complete_helicopter_uses: list[CompleteHelicopterUse]
) -> list[CompleteHelicopterUse]:
    logger.info(f"User(pk={user.pk}) is approving {complete_helicopter_uses}.")

    for complete_helicopter_use in complete_helicopter_uses:
        if complete_helicopter_use.well_planner != well_planner:
            logger.info(
                f"Unable to approve CompleteHelicopterUse(pk={complete_helicopter_use.pk}). "
                f"CompleteHelicopterUse does not belong to WellPlanner(pk={well_planner.pk})."
            )
            raise ValidationError("Chosen helicopter is not a valid choice.")

        complete_helicopter_use.approved = True
        complete_helicopter_use.save()

    logger.info(f"{complete_helicopter_uses} have been approved.")
    return complete_helicopter_uses


@transaction.atomic
@require_well_step(
    allowed_steps=[
        WellPlannerWizardStep.WELL_REVIEWING,
        WellPlannerWizardStep.WELL_REPORTING,
    ],
    error='Vessel use cannot be approved right now.',
)
def approve_well_planner_complete_vessel_uses(
    *, user: User, well_planner: WellPlanner, complete_vessel_uses: list[CompleteVesselUse]
) -> list[CompleteVesselUse]:
    logger.info(f"User(pk={user.pk}) is approving {complete_vessel_uses}.")

    for complete_vessel_use in complete_vessel_uses:
        if complete_vessel_use.well_planner != well_planner:
            logger.info(
                f"Unable to approve CompleteVesselUse(pk={complete_vessel_use.pk}). "
                f"CustomVesselUse does not belong to WellPlanner(pk={well_planner.pk})."
            )
            raise ValidationError("Chosen vessel is not a valid choice.")

        complete_vessel_use.approved = True
        complete_vessel_use.save()

    logger.info(f"{complete_vessel_uses} have been approved.")
    return complete_vessel_uses


@require_well_step(
    allowed_steps=[
        WellPlannerWizardStep.WELL_REVIEWING,
        WellPlannerWizardStep.WELL_REPORTING,
    ],
    error='Actual start date cannot be updated right now.',
)
def update_well_planner_actual_start_date(
    *, user: User, well_planner: WellPlanner, actual_start_date: datetime.date
) -> WellPlanner:
    logger.info(f"User(pk={user.pk}) is updating actual start date for WellPlanner(pk={well_planner.pk})")

    well_planner.actual_start_date = actual_start_date
    well_planner.save()

    logger.info("Actual start date has been changed.")
    return well_planner


def available_emission_reduction_initiatives(well_planner: WellPlanner) -> models.QuerySet[EmissionReductionInitiative]:
    emission_management_plan = well_planner.emission_management_plan
    if not emission_management_plan:
        return EmissionReductionInitiative.objects.none()

    return emission_management_plan.emission_reduction_initiatives.filter(
        deployment_date__lte=well_planner.planned_start_date,
        deleted=False,
    ).order_by('id')


def set_well_step_materials(
    *,
    well_step: WellPlannerCompleteStep | WellPlannerPlannedStep,
    materials: list[WellPlannerStepMaterialData],
) -> None:
    materials_to_delete = well_step.materials.exclude(
        pk__in=[material['id'] for material in materials if material.get('id') is not None]
    )

    for material in materials_to_delete:
        material.delete()
        logger.info(f"{material.__class__.__name__}(pk={material.pk}) has been deleted.")

    for material_data in materials:
        material_id = material_data.pop('id', None)  # type: ignore

        if material_id:
            well_step_material = well_step.materials.filter(pk=material_id).first()

            if not well_step_material:
                raise ValidationError({"materials": "Chosen materials is not a valid choice."})

            well_step_material.material_type = material_data['material_type']
            well_step_material.quantity = material_data['quantity']
            well_step_material.quota = material_data['quota']

            well_step_material.save()
            logger.info(f"{well_step_material.__class__.__name__}(pk={well_step_material.pk}) has been updated.")
        else:
            well_step_material = well_step.materials.create(
                material_type=material_data['material_type'],
                quantity=material_data['quantity'],
                quota=material_data['quota'],
            )
            logger.info(f"{well_step_material.__class__.__name__}(pk={well_step_material.pk}) has been created.")
