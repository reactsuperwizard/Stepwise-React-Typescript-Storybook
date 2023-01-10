import logging
import random
from typing import cast

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import transaction

from apps.projects.models import Plan, Project
from apps.projects.utils import GenericRigData, get_rig_model
from apps.rigs.models import (
    CustomDrillship,
    CustomJackupPlanCO2,
    CustomJackupRig,
    CustomSemiPlanCO2,
    CustomSemiRig,
    RigType,
)
from apps.studies.models import (
    StudyElement,
    StudyElementDrillshipRelation,
    StudyElementJackupRigRelation,
    StudyElementSemiRigRelation,
    StudyMetric,
)
from apps.tenants.models import User

logger = logging.getLogger(__name__)


@transaction.atomic
def delete_study_element(user: User, study_element: StudyElement) -> None:
    study_element_id = study_element.pk
    logger.info('User(pk=%s) is deleting StudyElement(pk=%s)', user.pk, study_element.pk)

    study_element.delete()

    logger.info('StudyElement(pk=%s) has been deleted', study_element_id)


RigsMap = dict[RigType, list[CustomSemiRig | CustomJackupRig | CustomDrillship]]


def get_study_rigs(project: Project, rigs: list[GenericRigData]) -> RigsMap:
    rigs_map: RigsMap = {RigType.SEMI: [], RigType.JACKUP: [], RigType.DRILLSHIP: []}

    for rig in rigs:
        rig_id = rig['id']
        rig_type = rig['type']
        try:
            rigs_map[rig_type].append(
                get_rig_model(rig_type).objects.filter(project=project, draft=False).get(pk=rig_id)
            )
        except ObjectDoesNotExist:
            logger.exception(
                'Unable to create study element. %s Rig(pk=%s) doesn\'t exist in Project(pk=%s)',
                rig_type,
                rig_id,
                project.id,
            )
            raise ValidationError({"rigs": f'{rig_type.capitalize()} Rig(pk={rig_id}) doesn\'t exist'})
        except KeyError:
            logger.exception(
                'Unable to create study element. Unknown rig type %s',
                rig_type,
            )
            raise ValidationError({"rigs": f'{rig_type.capitalize()} Rig(pk={rig_id}) doesn\'t exist'})

    return rigs_map


def create_study_element_rig_relation(
    *, rig_type: RigType, study_element: StudyElement, rig: CustomSemiRig | CustomJackupRig | CustomDrillship
) -> StudyElementSemiRigRelation | StudyElementJackupRigRelation | StudyElementDrillshipRelation:
    from apps.rigs.tasks import sync_custom_jackup_plan_co2_task, sync_custom_semi_plan_co2_task

    metric: StudyMetric = study_element.metric

    if rig_type not in metric.compatibility:
        raise ValidationError(
            {"metric": f"Metric '{metric.name}' is not compatible with {rig_type.capitalize()} rigs."}
        )

    if rig_type == RigType.SEMI:
        logger.info(
            f'Creating study element rig relation for CustomSemiRig(pk={rig.pk}) and StudyElement(pk={study_element.pk}).',
        )
        custom_semi_plan_co2, custom_semi_plan_co2_created = CustomSemiPlanCO2.objects.get_or_create(
            rig=rig,
            plan=study_element.plan,
        )
        study_element_semi_rig_relation = StudyElementSemiRigRelation.objects.create(
            study_element=study_element,
            rig=rig,
            value=None,
            rig_plan_co2=custom_semi_plan_co2,
        )

        if custom_semi_plan_co2_created:
            logger.info(
                f'Empty CustomSemiPlanCO2(pk={custom_semi_plan_co2.pk}) has been created. Delegating sync to a background task.',
            )
            transaction.on_commit(
                lambda: sync_custom_semi_plan_co2_task.delay(custom_semi_plan_co2.rig_id, custom_semi_plan_co2.plan_id)
            )
        else:
            logger.info(
                f'Using existing CustomSemiPlanCO2(pk={custom_semi_plan_co2.pk}).',
            )

        return study_element_semi_rig_relation

    elif rig_type == RigType.JACKUP:
        logger.info(
            f'Creating study element rig relation for CustomJackupRig(pk={rig.pk}) and StudyElement(pk={study_element.pk}).',
        )
        custom_jackup_plan_co2, custom_jackup_plan_co2_created = CustomJackupPlanCO2.objects.get_or_create(
            rig=rig,
            plan=study_element.plan,
        )
        study_element_jackup_rig_relation = StudyElementJackupRigRelation.objects.create(
            study_element=study_element,
            rig=rig,
            value=None,
            rig_plan_co2=custom_jackup_plan_co2,
        )

        if custom_jackup_plan_co2_created:
            logger.info(
                f'Empty CustomJackupPlanCO2(pk={custom_jackup_plan_co2.pk}) has been created. Delegating sync to a background task.',
            )
            transaction.on_commit(
                lambda: sync_custom_jackup_plan_co2_task.delay(
                    custom_jackup_plan_co2.rig_id, custom_jackup_plan_co2.plan_id
                )
            )
        else:
            logger.info(
                f'Using existing CustomJackupPlanCO2(pk={custom_jackup_plan_co2.pk}).',
            )

        return study_element_jackup_rig_relation

    elif rig_type == RigType.DRILLSHIP:
        return StudyElementDrillshipRelation.objects.create(
            study_element=study_element, rig=rig, value=random.randint(300, 600)
        )

    raise ValueError(f'Unknown rig type: {rig_type}')


@transaction.atomic
def create_study_element(
    *, user: User, project: Project, title: str, plan: Plan, metric: StudyMetric, rigs: list[GenericRigData]
) -> StudyElement:
    logger.info('User(pk=%s) is creating a new study element in Project(pk=%s)', user.pk, project.pk)

    if plan.project != project:
        logger.info(
            'Unable to create study element. Invalid project plan. Expected plan for Project(pk=%s) but received for Project(pk=%s)',
            project.pk,
            plan.project.pk,
        )
        raise ValidationError({"plan": f'Plan {plan.pk} doesn\'t exist'})

    if not rigs:
        logger.info('Unable to create study element. No rig provided')
        raise ValidationError({"rigs": 'At least one rig must be provided'})

    rigs_map = get_study_rigs(project, rigs)

    study_element = cast(
        StudyElement, StudyElement.objects.create(project=project, title=title, metric=metric, plan=plan, creator=user)
    )

    for rig_type, typed_rigs in rigs_map.items():
        for rig in typed_rigs:
            create_study_element_rig_relation(rig_type=rig_type, rig=rig, study_element=study_element)

    logger.info('StudyElement(pk=%s) has been created', study_element.pk)
    return study_element


@transaction.atomic
def update_study_element(
    *, user: User, study_element: StudyElement, title: str, plan: Plan, metric: StudyMetric, rigs: list[GenericRigData]
) -> StudyElement:
    logger.info('User(pk=%s) is updating StudyElement(pk=%s)', user.pk, study_element.pk)

    if plan.project != study_element.project:
        logger.info(
            'Unable to update study element. Invalid project plan. Expected plan for Project(pk=%s) but received for Project(pk=%s)',
            study_element.project_id,
            plan.project.pk,
        )
        raise ValidationError({"plan": f'Plan {plan.pk} doesn\'t exist'})

    if not rigs:
        logger.info('Unable to update study element. No rig provided')
        raise ValidationError({"rigs": 'At least one rig must be provided'})

    rigs_map = get_study_rigs(study_element.project, rigs)

    study_element.title = title
    study_element.metric = metric
    study_element.plan = plan
    study_element.save()

    study_element.semi_rigs.clear()
    study_element.jackup_rigs.clear()
    study_element.drillships.clear()

    for rig_type, typed_rigs in rigs_map.items():
        for rig in typed_rigs:
            create_study_element_rig_relation(rig_type=rig_type, rig=rig, study_element=study_element)

    logger.info('StudyElement(pk=%s) has been updated', study_element.pk)
    return study_element


@transaction.atomic
def swap_study_elements(
    *, user: User, project: Project, first_element: int, second_element: int
) -> tuple[StudyElement, StudyElement]:
    logger.info(
        'User(pk=%s) is swapping StudyElement(pk=%s) and StudyElement(pk=%s) in Project(pk=%s)',
        user.pk,
        first_element,
        second_element,
        project.pk,
    )

    try:
        first_study_element = StudyElement.objects.get(project=project, id=first_element)
    except StudyElement.DoesNotExist:
        logger.info(
            'Unable to swap study elements. StudyElement(pk=%s) doesn\'t exist in Project(pk=%s)',
            first_element,
            project.pk,
        )
        raise ValidationError({"first_element": f'Study element {first_element} doesn\'t exist'})

    try:
        second_study_element = StudyElement.objects.get(project=project, id=second_element)
    except StudyElement.DoesNotExist:
        logger.info(
            'Unable to swap study elements. StudyElement(pk=%s) doesn\'t exist in Project(pk=%s)',
            second_element,
            project.pk,
        )
        raise ValidationError({"second_element": f'Study element {second_element} doesn\'t exist'})

    first_study_element.swap(second_study_element)

    logger.info('Study elements have been swapped')

    return first_study_element, second_study_element
