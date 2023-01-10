import logging

from apps.app.celery import app
from apps.projects.models import Plan, Project
from apps.rigs.models import CustomJackupRig, CustomSemiRig
from apps.rigs.services import apis
from apps.studies.models import StudyElementJackupRigRelation, StudyElementSemiRigRelation
from apps.wells.models import CustomWell

logger = logging.getLogger(__name__)


@app.task
def sync_custom_jackup_plan_co2_task(custom_jackup_rig_id: int, plan_id: int) -> None:
    logger.info(
        f"Syncing co2 calculations for CustomJackupRig(pk={custom_jackup_rig_id}, draft=False) and Plan(pk={plan_id}) in the background."
    )

    try:
        custom_jackup_rig = CustomJackupRig.objects.get(pk=custom_jackup_rig_id, draft=False)
    except CustomJackupRig.DoesNotExist:
        logger.exception(
            f"Unable to sync all co2 calculations for CustomJackupRig(pk={custom_jackup_rig_id}, draft=False) and Plan(pk={plan_id}). Rig does not exist."
        )
        return

    try:
        plan = Plan.objects.get(pk=plan_id)
    except Plan.DoesNotExist:
        logger.exception(
            f"Unable to sync all co2 calculations for CustomJackupRig(pk={custom_jackup_rig_id}, draft=False) and Plan(pk={plan_id}). Plan does not exist."
        )
        return

    apis.sync_custom_jackup_plan_co2(custom_jackup_rig=custom_jackup_rig, plan=plan)
    logger.info(
        f"Co2 calculations for CustomJackupRig(pk={custom_jackup_rig_id}, draft=False) and Plan(pk={plan_id}) have been synced in the background."
    )


@app.task
def sync_custom_jackup_subarea_score_task(custom_jackup_rig_id: int) -> None:
    logger.info(f"Syncing subarea score for CustomJackupRig(pk={custom_jackup_rig_id}, draft=False) in the background.")

    try:
        custom_jackup_rig = CustomJackupRig.objects.get(pk=custom_jackup_rig_id, draft=False)
    except CustomJackupRig.DoesNotExist:
        logger.exception(
            f"Unable to sync subarea score for CustomJackupRig(pk={custom_jackup_rig_id}, draft=False). Rig does not exist."
        )
        return

    apis.sync_custom_jackup_subarea_score(custom_jackup_rig)

    for study_element in custom_jackup_rig.study_elements.all():
        sync_custom_jackup_plan_co2_task.delay(custom_jackup_rig.pk, study_element.plan_id)


@app.task
def sync_custom_semi_plan_co2_task(custom_semi_rig_id: int, plan_id: int) -> None:
    logger.info(
        f"Syncing co2 calculations for CustomSemiRig(pk={custom_semi_rig_id}, draft=False) and Plan(pk={plan_id}) in the background."
    )

    try:
        custom_semi_rig = CustomSemiRig.objects.get(pk=custom_semi_rig_id, draft=False)
    except CustomSemiRig.DoesNotExist:
        logger.exception(
            f"Unable to sync all co2 calculations for CustomSemiRig(pk={custom_semi_rig_id}, draft=False) and Plan(pk={plan_id}). Rig does not exist."
        )
        return

    try:
        plan = Plan.objects.get(pk=plan_id)
    except Plan.DoesNotExist:
        logger.exception(
            f"Unable to sync all co2 calculations for CustomSemiRig(pk={custom_semi_rig_id}, draft=False) and Plan(pk={plan_id}). Plan does not exist."
        )
        return

    apis.sync_custom_semi_plan_co2(custom_semi_rig=custom_semi_rig, plan=plan)
    logger.info(
        f"Co2 calculations for CustomSemiRig(pk={custom_semi_rig_id}, draft=False) and Plan(pk={plan_id}) have been synced in the background."
    )


@app.task
def sync_custom_semi_subarea_score_task(custom_semi_rig_id: int) -> None:
    logger.info(f"Syncing subarea score for CustomSemiRig(pk={custom_semi_rig_id}, draft=False) in the background.")

    try:
        custom_semi_rig = CustomSemiRig.objects.get(pk=custom_semi_rig_id, draft=False)
    except CustomSemiRig.DoesNotExist:
        logger.exception(
            f"Unable to sync subarea score for CustomSemiRig(pk={custom_semi_rig_id}, draft=False). Rig does not exist."
        )
        return

    apis.sync_custom_semi_subarea_score(custom_semi_rig)

    for study_element in custom_semi_rig.study_elements.all():
        sync_custom_semi_plan_co2_task.delay(custom_semi_rig.pk, study_element.plan_id)


@app.task
def sync_all_plan_co2_calculations_task(plan_id: int) -> None:
    logger.info(f"Syncing all co2 calculations related to Plan(pk={plan_id}) in the background.")
    try:
        plan = Plan.objects.get(pk=plan_id)
    except Plan.DoesNotExist:
        logger.exception(f"Unable to sync all co2 calculations related to Plan(pk={plan_id}). Plan does not exist.")
        return

    custom_jackup_rig_id_list = (
        StudyElementJackupRigRelation.objects.filter(study_element__plan=plan)
        .values_list('rig_id', flat=True)
        .distinct()
    )
    custom_semi_rig_id_list = (
        StudyElementSemiRigRelation.objects.filter(study_element__plan=plan).values_list('rig_id', flat=True).distinct()
    )

    for custom_jackup_rig_id in custom_jackup_rig_id_list:
        sync_custom_jackup_plan_co2_task.delay(custom_jackup_rig_id, plan.pk)

    for custom_semi_rig_id in custom_semi_rig_id_list:
        sync_custom_semi_plan_co2_task.delay(custom_semi_rig_id, plan.pk)


@app.task
def sync_all_custom_well_co2_calculations_task(custom_well_id: int) -> None:
    logger.info(
        f"Syncing all co2 calculations related to CustomWell(pk={custom_well_id}, draft=False) in the background."
    )

    try:
        custom_well = CustomWell.objects.get(pk=custom_well_id, draft=False)
    except CustomWell.DoesNotExist:
        logger.exception(
            f"Unable to sync all co2 calculations related to Well(pk={custom_well_id}, draft=False). Well does not exist."
        )
        return

    for plan in custom_well.plans.all():
        sync_all_plan_co2_calculations_task.delay(plan.pk)


@app.task
def sync_all_project_co2_calculations_task(project_id: int) -> None:
    logger.info(f"Syncing all co2 calculations related to Project(pk={project_id}) in the background.")
    try:
        project = Project.objects.get(pk=project_id)
    except Project.DoesNotExist:
        logger.exception(
            f"Unable to sync all co2 calculations related to Project(pk={project_id}). Project does not exist."
        )
        return

    for plan in project.plans.all():
        sync_all_plan_co2_calculations_task.delay(plan.pk)
