import logging
from typing import Any, TypedDict, cast

from black import List
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import transaction

from apps.projects.models import Plan, PlanWellRelation, Project
from apps.projects.utils import GenericRigData, get_rig_model
from apps.rigs.models import RigType
from apps.rigs.tasks import sync_all_plan_co2_calculations_task, sync_all_project_co2_calculations_task
from apps.tenants.models import Tenant, User
from apps.wells.models import CustomWell

logger = logging.getLogger(__name__)


class PlanWellData(TypedDict, total=False):
    id: int
    distance_from_previous_location: float
    distance_to_helicopter_base: float
    distance_to_psv_base: float
    distance_to_ahv_base: float
    distance_to_tug_base: float
    jackup_positioning_time: float
    semi_positioning_time: float
    operational_time: float


class PlanData(TypedDict, total=False):
    name: str
    description: str
    block_name: str
    reference_rig: GenericRigData
    distance_from_tug_base_to_previous_well: float
    wells: List[PlanWellData]


def create_project(
    *,
    tenant: Tenant,
    user: User,
    **data: Any,
) -> Project:
    logger.info(f'User(pk={user.pk}) is creating a new project in Tenant(pk={tenant.pk})')

    project = Project.objects.create(tenant=tenant, creator=user, **data)

    logger.info(f'Project(pk={project.pk}) has been created')
    return project


def update_project(
    *,
    project: Project,
    user: User,
    **data: Any,
) -> Project:
    logger.info(f'User(pk={user.pk}) is updating Project(pk={project.pk})')

    for field_name, field_value in data.items():
        setattr(project, field_name, field_value)
    project.save()

    sync_all_project_co2_calculations_task.delay(project.pk)
    logger.info('Project has been updated')
    return project


@transaction.atomic
def create_plan(
    *,
    user: User,
    project: Project,
    **kwargs: Any,
) -> Plan:
    data = cast(PlanData, kwargs)
    logger.info(f'User(pk={user.pk}) is creating a new plan in Project(pk={project.pk}).')
    wells: List[PlanWellData] = data.pop("wells")
    reference_rig_data: GenericRigData = data.pop("reference_rig")

    try:
        rig = (
            get_rig_model(reference_rig_data["type"])
            .objects.filter(project=project, draft=False)
            .studiable()  # type: ignore
            .get(pk=reference_rig_data["id"])
        )
    except ObjectDoesNotExist as e:
        logger.exception(
            'Unable to create a Plan. Custom%sRig(pk=%s) cannot be used as a reference rig.',
            reference_rig_data["type"].capitalize(),
            reference_rig_data["id"],
        )
        raise ValidationError({"reference_rig": "Invalid reference rig."}) from e

    new_plan_data = {
        **data,
        "reference_operation_jackup": rig if reference_rig_data["type"] == RigType.JACKUP else None,
        "reference_operation_semi": rig if reference_rig_data["type"] == RigType.SEMI else None,
        "reference_operation_drillship": rig if reference_rig_data["type"] == RigType.DRILLSHIP else None,
    }
    plan = Plan.objects.create(project=project, **new_plan_data)

    for order, well_data in enumerate(wells):
        well_id = well_data.pop("id")
        logger.info(f'Adding Well(pk={well_id}) to Plan(pk={plan.pk}).')

        try:
            well = plan.project.wells.get(pk=well_id, draft=False)
        except CustomWell.DoesNotExist:
            logger.info(
                f'Unable to add Well(pk={well_id}) to Plan(pk={plan.pk}). Well(pk={well_id}) does not belong to the project.'
            )
            raise ValidationError(f"Well(pk={well_id}) does not belong to the project.")

        plan_well = PlanWellRelation.objects.create(well=well, plan=plan, order=order, **well_data)
        logger.info(f'PlanWellRelation(pk={plan_well.pk}) has been created.')

    logger.info(f'Plan(pk={plan.pk}) has been created.')
    return plan


@transaction.atomic
def update_plan(
    *,
    user: User,
    plan: Plan,
    **kwargs: Any,
) -> Plan:
    data: PlanData = cast(PlanData, kwargs)
    logger.info(f'User(pk={user.pk}) is updating a Plan(pk={plan.pk}).')
    wells: List[PlanWellData] = data.pop("wells")
    well_ids = [well_data["id"] for well_data in wells]

    reference_rig_data: GenericRigData = data.pop("reference_rig")
    try:
        rig = (
            get_rig_model(reference_rig_data["type"])  # type: ignore
            .objects.filter(project=plan.project, draft=False)
            .studiable()
            .get(pk=reference_rig_data["id"])
        )
    except ObjectDoesNotExist as e:
        logger.exception(
            'Unable to update Plan(pk=%s). Custom%sRig(pk=%s) doesn\t belong to Project(pk=%s).',
            plan.pk,
            reference_rig_data["type"].capitalize(),
            reference_rig_data["id"],
            plan.project.pk,
        )
        raise ValidationError({"reference_rig": "Invalid reference rig."}) from e

    for field, value in data.items():
        setattr(plan, field, value)
    plan.reference_operation_jackup = rig if reference_rig_data["type"] == RigType.JACKUP else None
    plan.reference_operation_semi = rig if reference_rig_data["type"] == RigType.SEMI else None
    plan.reference_operation_drillship = rig if reference_rig_data["type"] == RigType.DRILLSHIP else None
    plan.save()

    plan_wells_to_delete = plan.plan_wells.filter(well__in=plan.wells.exclude(pk__in=well_ids))

    if plan_wells_to_delete.exists():
        logger.info(
            "Deleting %s.", ', '.join([f"PlanWellRelation(pk={plan_well.pk})" for plan_well in plan_wells_to_delete])
        )
        plan_wells_to_delete.delete()

    for order, well_data in enumerate(wells):
        well_id = well_data.pop("id")
        plan_well = plan.plan_wells.filter(well__pk=well_id, well__draft=False).first()

        if plan_well:
            logger.info(f'Updating PlanWellRelation(pk={plan_well.pk})')
            for field, value in well_data.items():
                setattr(plan_well, field, value)

            plan_well.order = order
            plan_well.save()
            logger.info(f'PlanWellRelation(pk={plan_well.pk}) has been updated.')
        else:
            logger.info(f'Adding Well(pk={well_id}) to Plan(pk={plan.pk}).')

            try:
                well = plan.project.wells.get(pk=well_id, draft=False)
            except CustomWell.DoesNotExist:
                logger.info(
                    f'Unable to add Well(pk={well_id}) to Plan(pk={plan.pk}). Well(pk={well_id}) does not belong to the project.'
                )
                raise ValidationError(f"Well(pk={well_id}) does not belong to the project.")

            plan_well = PlanWellRelation.objects.create(well=well, plan=plan, order=order, **well_data)
            logger.info(f'PlanWellRelation(pk={plan_well.pk}) has been created.')

    transaction.on_commit(lambda: sync_all_plan_co2_calculations_task.delay(plan.pk))
    logger.info(f'Plan(pk={plan.pk}) has been updated.')
    return plan


@transaction.atomic
def delete_project(*, user: User, project: Project) -> None:
    logger.info(f'User(pk={user.pk}) is deleting Project(pk={project.pk})')

    for rig in project.semi_rigs.filter(emp__isnull=False):
        assert rig.emp is not None
        logger.info(f'Deleting EMP(pk={rig.emp.pk})')
        rig.emp.delete()
    for rig in project.jackup_rigs.filter(emp__isnull=False):
        assert rig.emp is not None
        logger.info(f'Deleting EMP(pk={rig.emp.pk})')
        rig.emp.delete()
    for rig in project.drillships.filter(emp__isnull=False):
        assert rig.emp is not None
        logger.info(f'Deleting EMP(pk={rig.emp.pk})')
        rig.emp.delete()

    project.delete()

    logger.info('Project has been deleted')
