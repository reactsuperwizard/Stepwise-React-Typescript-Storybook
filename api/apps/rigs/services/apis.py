import logging
from typing import Any, cast

from django.core.exceptions import ValidationError

from apps.projects.models import Plan, Project
from apps.rigs.models import (
    CustomDrillship,
    CustomJackupPlanCO2,
    CustomJackupRig,
    CustomJackupSubareaScore,
    CustomSemiPlanCO2,
    CustomSemiRig,
    CustomSemiSubareaScore,
)
from apps.rigs.services.co2calculator import jackup as jackup_calculator
from apps.rigs.services.co2calculator import semi as semi_calculator
from apps.studies.models import StudyElementSemiRigRelation
from apps.tenants.models import Tenant, User

logger = logging.getLogger(__name__)


def create_custom_jackup_rig(tenant: Tenant, user: User, **data: Any) -> CustomJackupRig:
    logger.info(f'User(pk={user.pk}) is creating a new custom jakup rig in Tenant(pk={tenant.pk})')
    project_id = data.pop('project', None)
    project = None
    if project_id:
        try:
            project = Project.objects.get(tenant=tenant, pk=cast(int, project_id))
        except Project.DoesNotExist:
            raise ValidationError({"project": f'Project {project_id} doesn\'t exist'})

    rig = CustomJackupRig.objects.create(
        tenant=tenant,
        creator=user,
        project=project,
        **data,
    )

    logger.info(f'CustomJackupRig(pk={rig.pk}) has been created')
    return cast(CustomJackupRig, rig)


def create_custom_semi_rig(tenant: Tenant, user: User, **data: Any) -> CustomSemiRig:
    logger.info(f'User(pk={user.pk}) is creating a new custom semi rig in Tenant(pk={tenant.pk})')
    project_id = data.pop('project', None)
    project = None
    if project_id:
        try:
            project = Project.objects.get(tenant=tenant, pk=cast(int, project_id))
        except Project.DoesNotExist:
            raise ValidationError({"project": f'Project {project_id} doesn\'t exist'})
    rig = CustomSemiRig.objects.create(
        tenant=tenant,
        creator=user,
        project=project,
        **data,
    )

    logger.info(f'CustomSemiRig(pk={rig.pk}) has been created')
    return cast(CustomSemiRig, rig)


def update_custom_jackup_rig(rig: CustomJackupRig, user: User, **data: Any) -> CustomJackupRig:
    from apps.rigs.tasks import sync_custom_jackup_subarea_score_task

    logger.info(f'User(pk={user.pk}) is updating CustomJackupRig(pk={rig.pk})')

    if not rig.draft and data.get('draft'):
        raise ValidationError({"draft": 'Public rig cannot be marked as draft.'})

    for field_name, field_value in data.items():
        setattr(rig, field_name, field_value)
    rig.save()

    if not rig.draft:
        sync_custom_jackup_subarea_score_task.delay(rig.pk)
    logger.info('Custom jackup rig has been updated')
    return rig


def update_custom_semi_rig(rig: CustomSemiRig, user: User, **data: Any) -> CustomSemiRig:
    from apps.rigs.tasks import sync_custom_semi_subarea_score_task

    logger.info(f'User(pk={user.pk}) is updating CustomSemiRig(pk={rig.pk})')

    if not rig.draft and data.get('draft'):
        raise ValidationError({"draft": 'Public rig cannot be marked as draft.'})

    for field_name, field_value in data.items():
        setattr(rig, field_name, field_value)
    rig.save()

    if not rig.draft and not CustomSemiRig.objects.studiable().filter(pk=rig.pk).exists():  # type: ignore
        logger.info('Rig is not studiable. Removing all related study elements')
        StudyElementSemiRigRelation.objects.filter(rig=rig).delete()

    if not rig.draft:
        sync_custom_semi_subarea_score_task.delay(rig.pk)

    logger.info('Custom semi rig has been updated')
    return rig


def create_custom_drillship(tenant: Tenant, user: User, **data: Any) -> CustomDrillship:
    logger.info(f'User(pk={user.pk}) is creating a new custom drillship in Tenant(pk={tenant.pk})')
    project_id = data.pop('project', None)
    project = None
    if project_id:
        try:
            project = Project.objects.get(tenant=tenant, pk=cast(int, project_id))
        except Project.DoesNotExist:
            raise ValidationError({"project": f'Project {project_id} doesn\'t exist'})
    rig = CustomDrillship.objects.create(
        tenant=tenant,
        creator=user,
        project=project,
        **data,
    )
    return cast(CustomDrillship, rig)


def update_custom_drillship(rig: CustomDrillship, user: User, **data: Any) -> CustomDrillship:
    logger.info(f'User(pk={user.pk}) is updating CustomDrillship(pk={rig.pk})')

    if not rig.draft and data.get('draft'):
        raise ValidationError({"draft": 'Public rig cannot be marked as draft.'})

    for field_name, field_value in data.items():
        setattr(rig, field_name, field_value)
    rig.save()

    logger.info('Custom drillship has been updated')
    return rig


def delete_custom_rig(rig: CustomJackupRig | CustomSemiRig | CustomDrillship) -> None:
    plan: Plan | None = rig.plan_set.first()

    if plan:
        raise ValidationError(f'Rig cannot be deleted right now. Rig is used as a reference rig in plan "{plan.name}".')

    rig.delete()


def delete_custom_jackup_rig(user: User, rig: CustomJackupRig) -> None:
    logger.info(f'User(pk={user.pk}) is deleting CustomJackupRig(pk={rig.pk})')

    delete_custom_rig(rig)

    logger.info('Custom jackup rig has been deleted')


def delete_custom_semi_rig(user: User, rig: CustomSemiRig) -> None:
    logger.info(f'User(pk={user.pk}) is deleting CustomSemiRig(pk={rig.pk})')

    delete_custom_rig(rig)

    logger.info('Custom semi rig has been deleted')


def delete_custom_drillship(user: User, rig: CustomDrillship) -> None:
    logger.info(f'User(pk={user.pk}) is deleting CustomDrillship(pk={rig.pk})')

    delete_custom_rig(rig)

    logger.info('Custom drillship has been deleted')


def sync_custom_jackup_subarea_score(custom_jackup_rig: CustomJackupRig) -> CustomJackupSubareaScore:
    logger.info(f"Syncing jackup subarea score for CustomJackupRig(pk={custom_jackup_rig.pk}).")

    jackup_subarea_score, jackup_subarea_score_created = CustomJackupSubareaScore.objects.update_or_create(
        rig=custom_jackup_rig,
        defaults={
            "rig_status": jackup_calculator.calculate_custom_jackup_rig_status_score(custom_jackup_rig),
            "topside_efficiency": jackup_calculator.calculate_custom_jackup_topside_efficiency_score(custom_jackup_rig),
            "deck_efficiency": jackup_calculator.calculate_custom_jackup_deck_efficiency_score(custom_jackup_rig),
            "move_and_installation": jackup_calculator.calculate_custom_jackup_move_and_installation_score(
                custom_jackup_rig
            ),
            "capacities": jackup_calculator.calculate_custom_jackup_capacities_score(custom_jackup_rig),
            "co2": jackup_calculator.calculate_custom_jackup_co2_score(custom_jackup_rig),
        },
    )

    if jackup_subarea_score_created:
        logger.info(f"Created CustomJackupSubareaScore(pk={jackup_subarea_score.pk}).")
    else:
        logger.info(f"Updated CustomJackupSubareaScore(pk={jackup_subarea_score.pk}).")

    return jackup_subarea_score


def sync_custom_semi_subarea_score(custom_semi_rig: CustomSemiRig) -> CustomSemiSubareaScore:
    logger.info(f"Syncing semi subarea score for CustomSemiRig(pk={custom_semi_rig.pk}).")

    semi_subarea_score, semi_subarea_score_created = CustomSemiSubareaScore.objects.update_or_create(
        rig=custom_semi_rig,
        defaults={
            "rig_status": semi_calculator.calculate_custom_semi_rig_status_score(custom_semi_rig),
            "topside_efficiency": semi_calculator.calculate_custom_semi_topside_efficiency_score(custom_semi_rig),
            "deck_efficiency": semi_calculator.calculate_custom_semi_deck_efficiency_score(custom_semi_rig),
            "wow": semi_calculator.calculate_custom_semi_wow_score(custom_semi_rig),
            "capacities": semi_calculator.calculate_custom_semi_capacities_score(custom_semi_rig),
            "co2": semi_calculator.calculate_custom_semi_co2_score(custom_semi_rig),
        },
    )

    if semi_subarea_score_created:
        logger.info(f"Created CustomSemiSubareaScore(pk={semi_subarea_score.pk}).")
    else:
        logger.info(f"Updated CustomSemiSubareaScore(pk={semi_subarea_score.pk}).")

    return semi_subarea_score


class TotalJackupCO2Result(jackup_calculator.JackupCO2PerWellResult):
    total_tvd_from_msl: float


def sync_custom_jackup_plan_co2(*, custom_jackup_rig: CustomJackupRig, plan: Plan) -> CustomJackupPlanCO2:
    logger.info(f"Syncing jackup plan co2 for CustomJackupRig(pk={custom_jackup_rig.pk}) and Plan(pk={plan.pk}).")

    total_jackup_co2_result = TotalJackupCO2Result(
        fuel=0,
        co2_td=0,
        fuel_winter=0,
        co2_winter_td=0,
        fuel_summer=0,
        co2_summer_td=0,
        operational_days=0,
        move_time=0,
        total_days=0,
        rig_day_rate_usd_d=0,
        spread_cost=0,
        fuel_per_day=0,
        co2=0,
        psv_trips=0,
        psv_fuel=0,
        psv_co2=0,
        psv_cost_usd=0,
        helicopter_trips=0,
        helicopter_fuel=0,
        helicopter_co2=0,
        helicopter_cost_usd=0,
        move_fuel=0,
        tugs=0,
        tugs_cost=0,
        total_fuel=0,
        total_co2=0,
        total_cost=0,
        total_tvd_from_msl=0,
    )

    for well_index, plan_well_relation in enumerate(plan.plan_wells.order_by('order').all()):
        logger.info(f"Calculating jackup co2 for Well(pk={plan_well_relation.well.pk}).")

        custom_jackup_co2_per_well_result = jackup_calculator.calculate_custom_jackup_co2_per_well(
            plan=plan,
            plan_well=plan_well_relation,
            well_index=well_index,
            rig=custom_jackup_rig,
        )

        for key, value in custom_jackup_co2_per_well_result.items():
            total_jackup_co2_result[key] += value  # type: ignore
        total_jackup_co2_result["total_tvd_from_msl"] += plan_well_relation.well.tvd_from_msl

    cost_per_meter = 0.0
    if total_jackup_co2_result["total_tvd_from_msl"]:
        cost_per_meter = total_jackup_co2_result["total_cost"] / total_jackup_co2_result["total_tvd_from_msl"]

    custom_jackup_plan_co2, custom_jackup_plan_co2_created = custom_jackup_rig.co2_plans.update_or_create(
        plan=plan,
        defaults={
            "tugs_cost": total_jackup_co2_result["tugs_cost"],
            "helicopter_trips": total_jackup_co2_result["helicopter_trips"],
            "helicopter_fuel": total_jackup_co2_result["helicopter_fuel"],
            "helicopter_co2": total_jackup_co2_result["helicopter_co2"],
            "helicopter_cost": total_jackup_co2_result["helicopter_cost_usd"],
            "psv_trips": total_jackup_co2_result["psv_trips"],
            "psv_fuel": total_jackup_co2_result["psv_fuel"],
            "psv_cost": total_jackup_co2_result["psv_cost_usd"],
            "psv_co2": total_jackup_co2_result["psv_co2"],
            "total_fuel": total_jackup_co2_result["total_fuel"],
            "total_cost": total_jackup_co2_result["total_cost"],
            "total_co2": total_jackup_co2_result["total_co2"],
            "cost_per_meter": cost_per_meter,
            "total_days": total_jackup_co2_result["total_days"],
        },
    )

    if custom_jackup_plan_co2_created:
        logger.info(f"Created CustomJackupPlanCO2(pk={custom_jackup_plan_co2.pk}).")
    else:
        logger.info(f"Updated CustomJackupPlanCO2(pk={custom_jackup_plan_co2.pk}).")

    logger.info(
        f"Jackup plan co2 for CustomJackupRig(pk={custom_jackup_rig.pk}) and Plan(pk={plan.pk}) has been synced."
    )
    return custom_jackup_plan_co2


class TotalSemiCO2Result(semi_calculator.SemiCO2PerWellResult):
    total_tvd_from_msl: float


def sync_custom_semi_plan_co2(*, custom_semi_rig: CustomSemiRig, plan: Plan) -> CustomSemiPlanCO2:
    logger.info(f"Syncing semi plan co2 for CustomSemiRig(pk={custom_semi_rig.pk}) and Plan(pk={plan.pk}).")

    try:
        CustomSemiSubareaScore.objects.get(rig=custom_semi_rig)
    except CustomSemiSubareaScore.DoesNotExist:
        sync_custom_semi_subarea_score(custom_semi_rig)

    total_semi_co2_result = TotalSemiCO2Result(
        operational_days=0,
        transit_time=0,
        total_days=0,
        rig_day_rate_usd_d=0,
        spread_cost=0,
        rig_fuel_per_day=0,
        rig_total_fuel=0,
        rig_total_co2=0,
        psv_trips=0,
        psv_fuel=0,
        psv_co2=0,
        psv_cost_usd=0,
        helicopter_trips=0,
        helicopter_fuel=0,
        helicopter_co2=0,
        helicopter_cost_usd=0,
        ahv_fuel=0,
        ahv_cost=0,
        transit_fuel=0,
        tugs=0,
        tugs_cost=0,
        total_fuel=0,
        total_co2=0,
        total_cost=0,
        logistic_cost=0,
        move_cost=0,
        total_rig_and_spread_cost=0,
        total_fuel_cost=0,
        transit_co2=0,
        support_co2=0,
        total_tvd_from_msl=0,
    )

    for well_index, plan_well in enumerate(plan.plan_wells.order_by('order').all()):
        logger.info(f"Calculating semi co2 for Well(pk={plan_well.well_id}).")

        custom_semi_co2_per_well_result = semi_calculator.calculate_custom_semi_co2_per_well(
            plan=plan,
            plan_well=plan_well,
            rig=custom_semi_rig,
        )

        for key, value in custom_semi_co2_per_well_result.items():
            total_semi_co2_result[key] += value  # type: ignore
        total_semi_co2_result["total_tvd_from_msl"] += plan_well.well.tvd_from_msl

    cost_per_meter = 0.0
    if total_semi_co2_result["total_tvd_from_msl"]:
        cost_per_meter = total_semi_co2_result["total_cost"] / total_semi_co2_result["total_tvd_from_msl"]

    custom_semi_plan_co2, custom_semi_plan_co2_created = custom_semi_rig.co2_plans.update_or_create(
        plan=plan,
        defaults={
            "ahv_cost": total_semi_co2_result["ahv_cost"],
            "helicopter_trips": total_semi_co2_result["helicopter_trips"],
            "helicopter_fuel": total_semi_co2_result["helicopter_fuel"],
            "helicopter_co2": total_semi_co2_result["helicopter_co2"],
            "helicopter_cost": total_semi_co2_result["helicopter_cost_usd"],
            "psv_trips": total_semi_co2_result["psv_trips"],
            "psv_fuel": total_semi_co2_result["psv_fuel"],
            "psv_cost": total_semi_co2_result["psv_cost_usd"],
            "psv_co2": total_semi_co2_result["psv_co2"],
            "tugs_cost": total_semi_co2_result["tugs_cost"],
            "total_fuel": total_semi_co2_result["total_fuel"],
            "total_cost": total_semi_co2_result["total_cost"],
            "total_co2": total_semi_co2_result["total_co2"],
            "total_logistic_cost": total_semi_co2_result["logistic_cost"],
            "total_move_cost": total_semi_co2_result["move_cost"],
            "total_fuel_cost": total_semi_co2_result["total_fuel_cost"],
            "total_transit_co2": total_semi_co2_result["transit_co2"],
            "total_support_co2": total_semi_co2_result["support_co2"],
            "total_rig_and_spread_cost": total_semi_co2_result["total_rig_and_spread_cost"],
            "cost_per_meter": cost_per_meter,
            "total_days": total_semi_co2_result["total_days"],
        },
    )

    if custom_semi_plan_co2_created:
        logger.info(f"Created CustomSemiPlanCO2(pk={custom_semi_plan_co2.pk}).")
    else:
        logger.info(f"Updated CustomSemiPlanCO2(pk={custom_semi_plan_co2.pk}).")

    logger.info(f"Semi plan co2 for CustomSemiRig(pk={custom_semi_rig.pk}) and Plan(pk={plan.pk}) has been synced.")
    return custom_semi_plan_co2
