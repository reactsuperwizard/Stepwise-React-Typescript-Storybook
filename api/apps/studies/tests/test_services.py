from unittest.mock import MagicMock, call

import pytest
from django.core.exceptions import ValidationError

from apps.projects.factories import PlanFactory, ProjectFactory
from apps.rigs.factories import (
    AnyCustomRigFactory,
    CustomDrillshipFactory,
    CustomJackupPlanCO2Factory,
    CustomJackupRigFactory,
    CustomSemiPlanCO2Factory,
    CustomSemiRigFactory,
)
from apps.rigs.models import CustomJackupPlanCO2, CustomSemiPlanCO2, RigType
from apps.studies.factories import (
    StudyElementDrillshipRelationFactory,
    StudyElementFactory,
    StudyElementJackupRigRelationFactory,
    StudyElementSemiRigRelationFactory,
    StudyMetricFactory,
)
from apps.studies.models import StudyElement, StudyElementJackupRigRelation, StudyElementSemiRigRelation
from apps.studies.services import (
    create_study_element,
    delete_study_element,
    get_study_rigs,
    swap_study_elements,
    update_study_element,
)
from apps.tenants.factories import UserFactory


@pytest.mark.django_db
class TestDeleteStudyElement:
    def test_delete_study_element(self):
        user = UserFactory()
        first_study_element, second_study_element = StudyElementFactory.create_batch(2)
        StudyElementSemiRigRelationFactory(study_element=first_study_element)
        StudyElementJackupRigRelationFactory(study_element=second_study_element)

        delete_study_element(study_element=first_study_element, user=user)

        assert StudyElement.objects.filter(pk=first_study_element.pk).exists() is False
        assert StudyElement.objects.filter(pk=second_study_element.pk).exists() is True
        assert StudyElementSemiRigRelation.objects.count() == 0
        assert StudyElementJackupRigRelation.objects.count() == 1

    def test_reorder_on_delete(self):
        user = UserFactory()
        project = ProjectFactory()
        first_study_element, second_study_element, third_study_element = StudyElementFactory.create_batch(
            3, project=project
        )

        assert first_study_element.order == 0
        assert second_study_element.order == 1
        assert third_study_element.order == 2

        delete_study_element(study_element=second_study_element, user=user)
        first_study_element.refresh_from_db()
        third_study_element.refresh_from_db()

        assert first_study_element.order == 0
        assert third_study_element.order == 1


@pytest.mark.django_db(transaction=True)
class TestCreateStudyElement:
    def test_create_study_element(
        self,
        mock_sync_custom_jackup_plan_co2_task: MagicMock,
        mock_sync_custom_semi_plan_co2_task: MagicMock,
    ):
        user = UserFactory()
        project = ProjectFactory()
        plan = PlanFactory(project=project)

        jackup_rig_with_plan_calculation = CustomJackupRigFactory(project=project)
        jackup_rig_without_plan_calculation = CustomJackupRigFactory(project=project)
        custom_jackup_plan_co2 = CustomJackupPlanCO2Factory(rig=jackup_rig_with_plan_calculation, plan=plan)

        semi_rig_with_plan_calculation = CustomSemiRigFactory(project=project)
        semi_rig_without_plan_calculation = CustomSemiRigFactory(project=project)
        custom_semi_plan_co2 = CustomSemiPlanCO2Factory(rig=semi_rig_with_plan_calculation, plan=plan)

        drillship = CustomDrillshipFactory(project=project)

        metric = StudyMetricFactory()
        StudyElementFactory()
        StudyElementFactory(project=project)

        study_element = create_study_element(
            user=user,
            project=project,
            title="Test chart",
            plan=plan,
            metric=metric,
            rigs=[
                {'id': semi_rig_with_plan_calculation.pk, 'type': RigType.SEMI},
                {'id': semi_rig_without_plan_calculation.pk, 'type': RigType.SEMI},
                {'id': jackup_rig_with_plan_calculation.pk, 'type': RigType.JACKUP},
                {'id': jackup_rig_without_plan_calculation.pk, 'type': RigType.JACKUP},
                {'id': drillship.pk, 'type': RigType.DRILLSHIP},
            ],
        )

        assert study_element.project == project
        assert study_element.title == "Test chart"
        assert study_element.metric == metric
        assert study_element.plan == plan
        assert list(study_element.semi_rigs.order_by('id')) == [
            semi_rig_with_plan_calculation,
            semi_rig_without_plan_calculation,
        ]
        assert list(study_element.jackup_rigs.order_by('id')) == [
            jackup_rig_with_plan_calculation,
            jackup_rig_without_plan_calculation,
        ]
        assert study_element.drillships.get() == drillship
        assert study_element.creator == user
        assert study_element.order == 1

        study_element_semi_rig_relations = StudyElementSemiRigRelation.objects.all()
        assert study_element_semi_rig_relations[0].rig_plan_co2 == custom_semi_plan_co2
        assert study_element_semi_rig_relations[1].rig_plan_co2 == CustomSemiPlanCO2.objects.get(
            rig=semi_rig_without_plan_calculation.pk, plan=plan
        )

        study_element_jackup_rig_relations = StudyElementJackupRigRelation.objects.all()
        assert study_element_jackup_rig_relations[0].rig_plan_co2 == custom_jackup_plan_co2
        assert study_element_jackup_rig_relations[1].rig_plan_co2 == CustomJackupPlanCO2.objects.get(
            rig=jackup_rig_without_plan_calculation.pk, plan=plan
        )

        mock_sync_custom_semi_plan_co2_task.call_args_list == [call(semi_rig_without_plan_calculation.pk, plan.pk)]
        mock_sync_custom_jackup_plan_co2_task.call_args_list == [call(jackup_rig_without_plan_calculation.pk, plan.pk)]

    @pytest.mark.parametrize(
        "metric_data,CustomRigFactory, rig_type",
        (
            ({"is_jackup_compatible": False}, CustomJackupRigFactory, RigType.JACKUP),
            ({"is_semi_compatible": False}, CustomSemiRigFactory, RigType.SEMI),
            ({"is_drillship_compatible": False}, CustomDrillshipFactory, RigType.DRILLSHIP),
        ),
    )
    def test_metric_should_be_compatible_with_rigs(
        self,
        metric_data: dict,
        CustomRigFactory: AnyCustomRigFactory,
        rig_type: RigType,
    ):
        user = UserFactory()
        project = ProjectFactory()
        plan = PlanFactory(project=project)
        rig = CustomRigFactory(project=project)
        metric = StudyMetricFactory(**metric_data)

        with pytest.raises(ValidationError) as ex:
            create_study_element(
                user=user,
                project=project,
                title="Test chart",
                plan=plan,
                metric=metric,
                rigs=[
                    {'id': rig.pk, 'type': rig_type},
                ],
            )

        assert ex.value.message_dict == {
            "metric": [f"Metric '{metric.name}' is not compatible with {rig_type.capitalize()} rigs."]
        }

    def test_plan_must_belong_to_project(self):
        user = UserFactory()
        project = ProjectFactory()
        semi_rig = CustomSemiRigFactory(project=project)
        plan = PlanFactory()
        metric = StudyMetricFactory()

        with pytest.raises(ValidationError) as ex:
            create_study_element(
                user=user,
                project=project,
                title="Test chart",
                plan=plan,
                metric=metric,
                rigs=[
                    {'id': semi_rig.pk, 'type': RigType.SEMI},
                ],
            )

        assert ex.value.message_dict == {'plan': [f"Plan {plan.pk} doesn't exist"]}

    def test_study_element_must_include_at_least_one_rig(self):
        user = UserFactory()
        project = ProjectFactory()
        CustomSemiRigFactory(project=project)
        plan = PlanFactory(project=project)
        metric = StudyMetricFactory()

        with pytest.raises(ValidationError) as ex:
            create_study_element(user=user, project=project, title="Test chart", plan=plan, metric=metric, rigs=[])

        assert ex.value.message_dict == {'rigs': ["At least one rig must be provided"]}


@pytest.mark.django_db
class TestGetStudyRigs:
    def test_get_valid_rigs(self):
        project = ProjectFactory()
        jackup_rig = CustomJackupRigFactory(project=project)
        semi_rig = CustomSemiRigFactory(project=project)
        drillship = CustomDrillshipFactory(project=project)

        rigs_map = get_study_rigs(
            project=project,
            rigs=[
                {'id': semi_rig.pk, 'type': RigType.SEMI},
                {'id': jackup_rig.pk, 'type': RigType.JACKUP},
                {'id': drillship.pk, 'type': RigType.DRILLSHIP},
            ],
        )

        assert rigs_map == {RigType.SEMI: [semi_rig], RigType.JACKUP: [jackup_rig], RigType.DRILLSHIP: [drillship]}

    def test_reject_unknown_rigs(self):
        project = ProjectFactory()

        with pytest.raises(ValidationError) as ex:
            get_study_rigs(
                project=project,
                rigs=[{'id': 1, 'type': RigType.JACKUP}],
            )
        assert ex.value.message_dict == {'rigs': [f"{RigType.JACKUP.capitalize()} Rig(pk=1) doesn't exist"]}

    @pytest.mark.parametrize(
        'RigFactory, rig_type',
        (
            (CustomJackupRigFactory, RigType.JACKUP),
            (CustomSemiRigFactory, RigType.SEMI),
            (CustomDrillshipFactory, RigType.DRILLSHIP),
        ),
    )
    def test_reject_draft_rigs(self, RigFactory, rig_type):
        project = ProjectFactory()
        rig = RigFactory(draft=True, project=project)

        with pytest.raises(ValidationError) as ex:
            get_study_rigs(
                project=project,
                rigs=[{'id': rig.pk, 'type': rig_type}],
            )
        assert ex.value.message_dict == {'rigs': [f"{rig_type.capitalize()} Rig(pk={rig.pk}) doesn't exist"]}


@pytest.mark.django_db(transaction=True)
class TestUpdateStudyElement:
    def test_update_study_element(
        self,
        mock_sync_custom_jackup_plan_co2_task: MagicMock,
        mock_sync_custom_semi_plan_co2_task: MagicMock,
    ):
        user = UserFactory()
        creator = UserFactory()
        project = ProjectFactory()
        plan = PlanFactory(project=project)
        (
            old_jackup_rig,
            new_jackup_rig_without_plan_calculation,
            new_jackup_rig_with_plan_calculation,
        ) = CustomJackupRigFactory.create_batch(3, project=project)
        CustomJackupPlanCO2Factory(rig=new_jackup_rig_with_plan_calculation, plan=plan)

        (
            old_semi_rig,
            new_semi_rig_without_plan_calculation,
            new_semi_rig_with_plan_calculation,
        ) = CustomSemiRigFactory.create_batch(3, project=project)
        CustomSemiPlanCO2Factory(rig=new_semi_rig_with_plan_calculation, plan=plan)

        old_drillship, new_drillship = CustomDrillshipFactory.create_batch(2, project=project)

        metric = StudyMetricFactory()
        StudyElementFactory()
        StudyElementFactory(project=project)
        study_element = StudyElementFactory(title="Old chart", creator=creator, project=project)
        StudyElementSemiRigRelationFactory(study_element=study_element, rig=old_semi_rig)
        StudyElementJackupRigRelationFactory(study_element=study_element, rig=old_jackup_rig)
        StudyElementDrillshipRelationFactory(study_element=study_element, rig=old_drillship)

        study_element = update_study_element(
            user=user,
            study_element=study_element,
            title="Updated chart",
            plan=plan,
            metric=metric,
            rigs=[
                {'id': new_semi_rig_with_plan_calculation.pk, 'type': RigType.SEMI},
                {'id': new_semi_rig_without_plan_calculation.pk, 'type': RigType.SEMI},
                {'id': new_jackup_rig_with_plan_calculation.pk, 'type': RigType.JACKUP},
                {'id': new_jackup_rig_without_plan_calculation.pk, 'type': RigType.JACKUP},
                {'id': new_drillship.pk, 'type': RigType.DRILLSHIP},
            ],
        )

        assert study_element.project == project
        assert study_element.title == "Updated chart"
        assert study_element.metric == metric
        assert study_element.plan == plan
        assert list(study_element.semi_rigs.order_by('id')) == [
            new_semi_rig_without_plan_calculation,
            new_semi_rig_with_plan_calculation,
        ]
        assert list(study_element.jackup_rigs.order_by('id')) == [
            new_jackup_rig_without_plan_calculation,
            new_jackup_rig_with_plan_calculation,
        ]
        assert study_element.drillships.get() == new_drillship
        assert study_element.creator == creator
        assert study_element.order == 1

        CustomSemiPlanCO2.objects.get(rig=new_semi_rig_without_plan_calculation.pk, plan=plan)
        CustomJackupPlanCO2.objects.get(rig=new_jackup_rig_without_plan_calculation.pk, plan=plan)

        assert mock_sync_custom_semi_plan_co2_task.call_args_list == [
            call(new_semi_rig_without_plan_calculation.pk, plan.pk)
        ]
        assert mock_sync_custom_jackup_plan_co2_task.call_args_list == [
            call(new_jackup_rig_without_plan_calculation.pk, plan.pk)
        ]

    @pytest.mark.parametrize(
        "metric_data,CustomRigFactory, rig_type",
        (
            ({"is_jackup_compatible": False}, CustomJackupRigFactory, RigType.JACKUP),
            ({"is_semi_compatible": False}, CustomSemiRigFactory, RigType.SEMI),
            ({"is_drillship_compatible": False}, CustomDrillshipFactory, RigType.DRILLSHIP),
        ),
    )
    def test_metric_should_be_compatible_with_rigs(
        self,
        metric_data: dict,
        CustomRigFactory: AnyCustomRigFactory,
        rig_type: RigType,
    ):
        user = UserFactory()
        project = ProjectFactory()
        plan = PlanFactory(project=project)
        rig = CustomRigFactory(project=project)
        metric = StudyMetricFactory(**metric_data)
        study_element = StudyElementFactory(project=project)

        with pytest.raises(ValidationError) as ex:
            update_study_element(
                user=user,
                study_element=study_element,
                title="Test chart",
                plan=plan,
                metric=metric,
                rigs=[
                    {'id': rig.pk, 'type': rig_type},
                ],
            )

        assert ex.value.message_dict == {
            "metric": [f"Metric '{metric.name}' is not compatible with {rig_type.capitalize()} rigs."]
        }

    def test_plan_must_belong_to_project(self):
        user = UserFactory()
        semi_rig = CustomSemiRigFactory()
        study_element = StudyElementFactory()
        plan = PlanFactory()
        metric = StudyMetricFactory()

        with pytest.raises(ValidationError) as ex:
            update_study_element(
                user=user,
                study_element=study_element,
                title="Test chart",
                plan=plan,
                metric=metric,
                rigs=[
                    {'id': semi_rig.pk, 'type': RigType.SEMI},
                ],
            )

        assert ex.value.message_dict == {'plan': [f"Plan {plan.pk} doesn't exist"]}

    def test_study_element_must_include_at_least_one_rig(self):
        user = UserFactory()
        study_element = StudyElementFactory()
        plan = PlanFactory(project=study_element.project)
        metric = StudyMetricFactory()

        with pytest.raises(ValidationError) as ex:
            update_study_element(
                user=user, study_element=study_element, title="Test chart", plan=plan, metric=metric, rigs=[]
            )

        assert ex.value.message_dict == {'rigs': ["At least one rig must be provided"]}


@pytest.mark.django_db
class TestSwapStudyElements:
    def test_swap_study_elements(self):
        user = UserFactory()
        project = ProjectFactory()
        first_study_element, second_study_element, third_study_element = StudyElementFactory.create_batch(
            3, project=project
        )

        assert first_study_element.order == 0
        assert second_study_element.order == 1
        assert third_study_element.order == 2

        swap_study_elements(
            user=user, project=project, first_element=second_study_element.pk, second_element=third_study_element.pk
        )

        first_study_element.refresh_from_db()
        second_study_element.refresh_from_db()
        third_study_element.refresh_from_db()
        assert first_study_element.order == 0
        assert second_study_element.order == 2
        assert third_study_element.order == 1

    def test_first_element_must_belong_to_project(self):
        user = UserFactory()
        project = ProjectFactory()
        first_study_element = StudyElementFactory()
        second_study_element = StudyElementFactory(project=project)

        with pytest.raises(ValidationError) as ex:
            swap_study_elements(
                user=user, project=project, first_element=first_study_element.pk, second_element=second_study_element.pk
            )

        assert ex.value.message_dict == {'first_element': [f'Study element {first_study_element.pk} doesn\'t exist']}

    def test_second_element_must_belong_to_project(self):
        user = UserFactory()
        project = ProjectFactory()
        first_study_element = StudyElementFactory(project=project)
        second_study_element = StudyElementFactory()

        with pytest.raises(ValidationError) as ex:
            swap_study_elements(
                user=user, project=project, first_element=first_study_element.pk, second_element=second_study_element.pk
            )

        assert ex.value.message_dict == {'second_element': [f'Study element {second_study_element.pk} doesn\'t exist']}
