import datetime
from copy import deepcopy

import pytest
from django.core.exceptions import ValidationError

from apps.emps.factories import ConceptEMPElementFactory, CustomEMPElementFactory, EMPFactory
from apps.emps.models import EMP, ConceptEMPElement
from apps.emps.services import CustomEMPElementData, EMPData, create_emp, delete_emp, update_emp
from apps.rigs.factories import (
    AnyCustomRigFactory,
    CustomDrillshipFactory,
    CustomJackupRigFactory,
    CustomSemiRigFactory,
)
from apps.tenants.factories import UserFactory


@pytest.mark.django_db
@pytest.mark.parametrize("RigFactory", (CustomJackupRigFactory, CustomSemiRigFactory, CustomDrillshipFactory))
class TestCreateEMP:
    @pytest.fixture
    def concept_emp_element(self) -> ConceptEMPElement:
        return ConceptEMPElementFactory()

    @pytest.fixture
    def emp_data(self, concept_emp_element: ConceptEMPElement) -> EMPData:
        return EMPData(
            name="EMP name",
            description="EMP description",
            api_description="EMP api description",
            start_date=datetime.date.today(),
            end_date=datetime.date.today(),
            total_rig_baseline_average=10.0,
            total_rig_target_average=20.0,
            elements=[
                CustomEMPElementData(
                    concept_id=concept_emp_element.pk,
                    baseline_average=20.0,
                    target_average=100.0,
                ),
            ],
        )

    def test_should_create_emp(self, emp_data: EMPData, RigFactory: AnyCustomRigFactory):
        custom_rig = RigFactory(emp=None)
        user = UserFactory()

        emp = create_emp(user=user, custom_rig=custom_rig, **deepcopy(emp_data))

        assert emp.pk is not None
        assert emp.name == emp_data["name"]
        assert emp.description == emp_data["description"]
        assert emp.api_description == emp_data["api_description"]
        assert emp.start_date == emp_data["start_date"]
        assert emp.end_date == emp_data["start_date"]
        assert emp.total_rig_baseline_average == emp_data["total_rig_baseline_average"]
        assert emp.total_rig_target_average == emp_data["total_rig_target_average"]

        custom_emp_element = emp.elements.get()
        assert custom_emp_element.concept_emp_element.pk == emp_data["elements"][0]["concept_id"]
        assert custom_emp_element.baseline_average == emp_data["elements"][0]["baseline_average"]
        assert custom_emp_element.target_average == emp_data["elements"][0]["target_average"]

        custom_rig.refresh_from_db()
        assert custom_rig.emp == emp

    def test_should_raise_validation_error_for_rig_with_emp(self, emp_data: EMPData, RigFactory: AnyCustomRigFactory):
        user = UserFactory()
        custom_rig = RigFactory()

        with pytest.raises(ValidationError, match='EMP for this rig already exists'):
            create_emp(user=user, custom_rig=custom_rig, **emp_data)

    def test_should_raise_validation_error_for_non_existing_concept_element(
        self, emp_data: EMPData, RigFactory: AnyCustomRigFactory
    ):
        user = UserFactory()
        custom_rig = RigFactory(emp=None)
        emp_data["elements"][0]["concept_id"] = 999

        with pytest.raises(ValidationError, match='Concept emp element does not exist'):
            create_emp(user=user, custom_rig=custom_rig, **emp_data)

    def test_should_raise_validation_error_for_end_date_before_start_date(
        self, emp_data: EMPData, RigFactory: AnyCustomRigFactory
    ):
        user = UserFactory()
        custom_rig = RigFactory(emp=None)
        emp_data["end_date"] = emp_data["start_date"] - datetime.timedelta(days=1)

        with pytest.raises(ValidationError, match="End date can't be before start date."):
            create_emp(user=user, custom_rig=custom_rig, **emp_data)


@pytest.mark.django_db
class TestUpdateEMP:
    @pytest.fixture
    def emp(self) -> EMP:
        return EMPFactory()

    @pytest.fixture
    def emp_update_data(self, emp: EMP) -> EMPData:
        custom_emp_element = CustomEMPElementFactory(emp=emp)  # Should be updated
        CustomEMPElementFactory(emp=emp)  # Should be deleted

        return EMPData(
            name="Updated EMP name",
            description="Udpated EMP description",
            api_description="Updated EMP api description",
            start_date=datetime.date.today() + datetime.timedelta(days=1),
            end_date=datetime.date.today() + datetime.timedelta(days=2),
            total_rig_baseline_average=10.0,
            total_rig_target_average=20.0,
            elements=[
                CustomEMPElementData(
                    id=custom_emp_element.pk,
                    concept_id=custom_emp_element.concept_emp_element.pk,
                    baseline_average=20.0,
                    target_average=100.0,
                ),
                CustomEMPElementData(
                    concept_id=ConceptEMPElementFactory().pk,
                    baseline_average=20.0,
                    target_average=100.0,
                ),
            ],
        )

    def test_should_update_emp(self, emp: EMP, emp_update_data: EMPData):
        user = UserFactory()
        updated_emp = update_emp(user=user, emp=emp, **deepcopy(emp_update_data))

        assert updated_emp.name == emp_update_data["name"]
        assert updated_emp.description == emp_update_data["description"]
        assert updated_emp.api_description == emp_update_data["api_description"]
        assert updated_emp.start_date == emp_update_data["start_date"]
        assert updated_emp.end_date == emp_update_data["end_date"]
        assert updated_emp.total_rig_baseline_average == emp_update_data["total_rig_baseline_average"]
        assert updated_emp.total_rig_target_average == emp_update_data["total_rig_target_average"]

        custom_emp_elements = updated_emp.elements.all()

        assert custom_emp_elements.count() == 2
        assert custom_emp_elements[0].id == emp_update_data["elements"][0]["id"]
        assert custom_emp_elements[0].concept_emp_element_id == emp_update_data["elements"][0]["concept_id"]
        assert custom_emp_elements[0].baseline_average == emp_update_data["elements"][0]["baseline_average"]
        assert custom_emp_elements[0].target_average == emp_update_data["elements"][0]["target_average"]

        assert custom_emp_elements[1].concept_emp_element_id == emp_update_data["elements"][1]["concept_id"]
        assert custom_emp_elements[1].baseline_average == emp_update_data["elements"][1]["baseline_average"]
        assert custom_emp_elements[1].target_average == emp_update_data["elements"][1]["target_average"]

    def test_should_raise_validation_error_for_non_existing_custom_element_when_updating_element(
        self, emp: EMP, emp_update_data: EMPData
    ):
        user = UserFactory()
        custom_emp_element_id = emp_update_data["elements"][0]["id"]
        emp_update_data["elements"][0]["concept_id"] = 999

        with pytest.raises(
            ValidationError,
        ) as ex:
            update_emp(user=user, emp=emp, **emp_update_data)

        assert ex.value.messages == [
            f"CustomEMPElement(pk={custom_emp_element_id}, concept_emp_element_id=999) does not exist."
        ]

    def test_should_raise_validation_error_for_non_existing_concept_element_when_creating_element(
        self, emp: EMP, emp_update_data: EMPData
    ):
        user = UserFactory()
        emp_update_data["elements"][1]["concept_id"] = 999

        with pytest.raises(ValidationError) as ex:
            update_emp(user=user, emp=emp, **emp_update_data)

        assert ex.value.messages == ["ConceptEMPElement(pk=999) does not exist."]

    def test_should_raise_validation_error_for_end_date_before_start_date(self, emp: EMP, emp_update_data: EMPData):
        user = UserFactory()
        emp_update_data["end_date"] = emp_update_data["start_date"] - datetime.timedelta(days=1)

        with pytest.raises(ValidationError, match="End date can't be before start date."):
            update_emp(user=user, emp=emp, **emp_update_data)


@pytest.mark.django_db
class TestDeleteEMP:
    def test_should_delete_emp(self):
        user = UserFactory()
        emp = EMPFactory()

        delete_emp(user=user, emp=emp)

        with pytest.raises(EMP.DoesNotExist):
            EMP.objects.get(pk=emp.pk)
