import datetime
import logging
from typing import TypedDict

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.emps.models import EMP, ConceptEMPElement, CustomEMPElement
from apps.rigs.models import CustomDrillship, CustomJackupRig, CustomSemiRig
from apps.tenants.models import User

logger = logging.getLogger(__name__)


class CustomEMPElementData(TypedDict):
    id: int | None
    concept_id: int
    baseline_average: float
    target_average: float


class EMPData(TypedDict):
    name: str
    description: str
    api_description: str
    start_date: datetime.date
    end_date: datetime.date
    total_rig_baseline_average: float
    total_rig_target_average: float
    elements: list[CustomEMPElementData]


@transaction.atomic
def create_emp(*, user: User, custom_rig: CustomJackupRig | CustomSemiRig | CustomDrillship, **data: EMPData) -> EMP:
    logger.info(f'User(pk={user.pk}) is creating an EMP for {custom_rig.__class__.__name__}(pk={custom_rig.pk})')

    if custom_rig.emp is not None:
        logger.info(
            f'Unable to create EMP. EMP for {custom_rig.__class__.__name__}(pk={custom_rig.pk}) already exists.'
        )
        raise ValidationError("EMP for this rig already exists")

    element_data_list: list[CustomEMPElementData] = data.pop("elements")  # type: ignore

    if data["end_date"] < data["start_date"]:  # type: ignore
        logger.info('Unable to create EMP. End date before start date.')
        raise ValidationError({"end_date": "End date can't be before start date."})

    emp: EMP = EMP.objects.create(**data)

    for element_data in element_data_list:
        concept_id: int = element_data.pop("concept_id")  # type: ignore
        logger.info(f'Adding ConceptEMPElement(pk={concept_id}) to EMP(pk={emp.pk}).')

        try:
            concept_emp_element = ConceptEMPElement.objects.get(pk=concept_id)
        except ConceptEMPElement.DoesNotExist:
            logger.info(f'Unable to add ConceptEMPElement(pk={concept_id}). ConceptEMPElement does not exist.')
            raise ValidationError({"concept_id": "Concept emp element does not exist"})

        CustomEMPElement.objects.create(
            emp=emp,
            concept_emp_element=concept_emp_element,
            baseline_average=element_data["baseline_average"],
            target_average=element_data["target_average"],
        )

    custom_rig.emp = emp
    custom_rig.save()

    logger.info(f'EMP(pk={emp.pk}) has been created.')
    return emp


@transaction.atomic
def update_emp(*, user: User, emp: EMP, **data: EMPData) -> EMP:
    logger.info(f'User(pk={user.pk}) is updating an EMP(pk={emp.pk})')
    element_data_list: list[CustomEMPElementData] = data.pop("elements")  # type: ignore
    element_data_id_list: list[int] = [
        element_data["id"]
        for element_data in element_data_list
        if "id" in element_data and element_data["id"] is not None
    ]
    custom_emp_elements_to_delete = emp.elements.exclude(pk__in=element_data_id_list)

    if data["end_date"] < data["start_date"]:  # type: ignore
        logger.info('Unable to create EMP. End date before start date.')
        raise ValidationError({"end_date": "End date can't be before start date."})

    for field, value in data.items():
        setattr(emp, field, value)

    emp.save()

    if custom_emp_elements_to_delete.exists():
        for element_to_delete in custom_emp_elements_to_delete:
            logger.info("Deleting CustomEMPElement(pk={element_to_delete.pk})")
            element_to_delete.delete()

    for element_data in element_data_list:
        custom_emp_element_id = element_data.pop("id", None)  # type: ignore
        concept_emp_element_id: int = element_data.pop("concept_id")  # type: ignore

        if custom_emp_element_id is not None:
            logger.info(f"Upadting CustomEMPElement(pk={custom_emp_element_id}).")
            try:
                custom_emp_element: CustomEMPElement = CustomEMPElement.objects.get(
                    pk=custom_emp_element_id, concept_emp_element_id=concept_emp_element_id
                )
            except CustomEMPElement.DoesNotExist:
                logger.info(
                    f"Unable to update CustomEMPElement(pk={custom_emp_element_id}, concept_emp_element_id={concept_emp_element_id}). CustomEMPElement does not exist."
                )
                raise ValidationError(
                    f"CustomEMPElement(pk={custom_emp_element_id}, concept_emp_element_id={concept_emp_element_id}) does not exist."
                )

            for field, value in element_data.items():  # type: ignore
                setattr(custom_emp_element, field, value)

        else:
            logger.info(f"Creating CustomEMPElement for ConceptEMPElement(pk={concept_emp_element_id})")

            try:
                concept_emp_element = ConceptEMPElement.objects.get(pk=concept_emp_element_id)
            except ConceptEMPElement.DoesNotExist:
                logger.info(
                    "Unable create CustomEMPElement. ConceptEMPElement(pk={concept_emp_element_id}) does not exist."
                )
                raise ValidationError(f"ConceptEMPElement(pk={concept_emp_element_id}) does not exist.")

            custom_emp_element = CustomEMPElement(emp=emp, concept_emp_element=concept_emp_element, **element_data)

        custom_emp_element.save()

    logger.info(f"EMP(pk={emp.pk}) has been updated.")
    return emp


def delete_emp(*, user: User, emp: EMP) -> None:
    logger.info(f"User(pk={user.pk}) is deleting EMP(pk={emp.pk}.")
    emp.delete()
    logger.info(f"EMP(pk={emp.pk}) has been deleted.")
