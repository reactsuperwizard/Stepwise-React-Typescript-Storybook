from unittest.mock import MagicMock, call

import pytest
from celery import states

from apps.projects.factories import PlanFactory, PlanWellRelationFactory, ProjectFactory
from apps.rigs.factories import CustomJackupRigFactory, CustomSemiRigFactory
from apps.rigs.models import (
    CustomJackupPlanCO2,
    CustomJackupRig,
    CustomJackupSubareaScore,
    CustomSemiPlanCO2,
    CustomSemiRig,
    CustomSemiSubareaScore,
)
from apps.rigs.tasks import (
    sync_all_custom_well_co2_calculations_task,
    sync_all_plan_co2_calculations_task,
    sync_all_project_co2_calculations_task,
    sync_custom_jackup_plan_co2_task,
    sync_custom_jackup_subarea_score_task,
    sync_custom_semi_plan_co2_task,
    sync_custom_semi_subarea_score_task,
)
from apps.studies.factories import StudyElementJackupRigRelationFactory, StudyElementSemiRigRelationFactory
from apps.wells.factories import CustomWellFactory


@pytest.mark.django_db
class TestSyncCustomJackupPlanCO2Task:
    def test_should_sync_custom_jackup_plan_co2(self, concept_cj70: CustomJackupRig):
        with pytest.raises(CustomJackupSubareaScore.DoesNotExist):
            CustomJackupSubareaScore.objects.get(rig=concept_cj70)

        plan_well_relation = PlanWellRelationFactory()
        result = sync_custom_jackup_plan_co2_task.apply(args=(concept_cj70.pk, plan_well_relation.plan.pk))

        assert result.get() is None
        assert result.state == states.SUCCESS

        concept_cj70.refresh_from_db()
        assert CustomJackupSubareaScore.objects.filter(rig=concept_cj70).exists()
        custom_jackup_plan_co2 = CustomJackupPlanCO2.objects.get()
        assert custom_jackup_plan_co2.rig == concept_cj70
        assert custom_jackup_plan_co2.plan == plan_well_relation.plan


@pytest.mark.django_db
class TestSyncCustomJackupSubareaScoreTask:
    def test_should_sync_custom_jackup_subarea_score(
        self,
        mock_sync_custom_jackup_plan_co2_task: MagicMock,
        concept_cj70: CustomJackupRig,
    ):
        with pytest.raises(CustomJackupSubareaScore.DoesNotExist):
            CustomJackupSubareaScore.objects.get(rig=concept_cj70)

        plan_1 = StudyElementJackupRigRelationFactory(rig=concept_cj70).study_element.plan
        plan_2 = StudyElementJackupRigRelationFactory(rig=concept_cj70).study_element.plan
        StudyElementJackupRigRelationFactory()

        result = sync_custom_jackup_subarea_score_task.apply(args=(concept_cj70.pk,))

        assert result.get() is None
        assert result.state == states.SUCCESS

        concept_cj70.refresh_from_db()
        assert CustomJackupSubareaScore.objects.filter(rig=concept_cj70).exists()

        assert mock_sync_custom_jackup_plan_co2_task.call_args_list == [
            call(concept_cj70.pk, plan_1.pk),
            call(concept_cj70.pk, plan_2.pk),
        ]

    def test_should_not_sync_draft_rig(self, mock_sync_custom_jackup_plan_co2_task: MagicMock):
        custom_jackup_rig_draft = CustomJackupRigFactory(draft=True)
        StudyElementJackupRigRelationFactory(rig=custom_jackup_rig_draft)

        result = sync_custom_jackup_subarea_score_task.apply(args=(custom_jackup_rig_draft.pk,))

        assert result.get() is None
        assert result.state == states.SUCCESS

        assert CustomJackupSubareaScore.objects.filter(rig=custom_jackup_rig_draft).exists() is False
        mock_sync_custom_jackup_plan_co2_task.assert_not_called()


@pytest.mark.django_db
class TestSyncCustomSemiPlanCO2Task:
    def test_should_sync_custom_semi_plan_co2(self, concept_cs60: CustomSemiRig):
        with pytest.raises(CustomSemiSubareaScore.DoesNotExist):
            CustomSemiSubareaScore.objects.get(rig=concept_cs60)

        plan_well_relation = PlanWellRelationFactory()
        result = sync_custom_semi_plan_co2_task.apply(args=(concept_cs60.pk, plan_well_relation.plan.pk))

        assert result.get() is None
        assert result.state == states.SUCCESS

        concept_cs60.refresh_from_db()
        assert CustomSemiSubareaScore.objects.filter(rig=concept_cs60).exists()
        custom_semi_plan_co2 = CustomSemiPlanCO2.objects.get()
        assert custom_semi_plan_co2.rig == concept_cs60
        assert custom_semi_plan_co2.plan == plan_well_relation.plan


@pytest.mark.django_db
class TestSyncCustomSemiSubareaScoreTask:
    def test_should_sync_custom_semi_subarea_score(
        self, mock_sync_custom_semi_plan_co2_task: MagicMock, concept_cs60: CustomSemiRig
    ):
        with pytest.raises(CustomSemiSubareaScore.DoesNotExist):
            CustomSemiSubareaScore.objects.get(rig=concept_cs60)

        plan_1 = StudyElementSemiRigRelationFactory(rig=concept_cs60).study_element.plan
        plan_2 = StudyElementSemiRigRelationFactory(rig=concept_cs60).study_element.plan
        StudyElementSemiRigRelationFactory()

        result = sync_custom_semi_subarea_score_task.apply(args=(concept_cs60.pk,))

        assert result.get() is None
        assert result.state == states.SUCCESS

        assert CustomSemiSubareaScore.objects.filter(rig=concept_cs60).exists()
        assert mock_sync_custom_semi_plan_co2_task.call_args_list == [
            call(concept_cs60.pk, plan_1.pk),
            call(concept_cs60.pk, plan_2.pk),
        ]

    def test_should_not_sync_draft_rig(self, mock_sync_custom_semi_plan_co2_task: MagicMock):
        custom_semi_rig_draft = CustomSemiRigFactory(draft=True)

        result = sync_custom_semi_subarea_score_task.apply(args=(custom_semi_rig_draft.pk,))

        assert result.get() is None
        assert result.state == states.SUCCESS

        assert CustomSemiSubareaScore.objects.filter(rig=custom_semi_rig_draft).exists() is False
        mock_sync_custom_semi_plan_co2_task.assert_not_called()


@pytest.mark.django_db
class TestSyncAllPlanCO2Calculations:
    def test_should_sync_all_plan_co2_calculations(
        self, mock_sync_custom_jackup_plan_co2_task: MagicMock, mock_sync_custom_semi_plan_co2_task: MagicMock
    ):
        plan = PlanFactory()
        (
            study_element_jackup_rig_relation_1,
            study_element_jackup_rig_relation_2,
        ) = StudyElementJackupRigRelationFactory.create_batch(2, study_element__plan=plan)
        StudyElementJackupRigRelationFactory()

        (
            study_element_semi_rig_relation_1,
            study_element_semi_rig_relation_2,
        ) = StudyElementSemiRigRelationFactory.create_batch(2, study_element__plan=plan)
        StudyElementSemiRigRelationFactory()

        result = sync_all_plan_co2_calculations_task.apply(args=(plan.pk,))

        assert result.get() is None
        assert result.state == states.SUCCESS
        assert mock_sync_custom_jackup_plan_co2_task.call_args_list == [
            call(study_element_jackup_rig_relation_1.rig.pk, plan.pk),
            call(study_element_jackup_rig_relation_2.rig.pk, plan.pk),
        ]
        assert mock_sync_custom_semi_plan_co2_task.call_args_list == [
            call(study_element_semi_rig_relation_1.rig.pk, plan.pk),
            call(study_element_semi_rig_relation_2.rig.pk, plan.pk),
        ]


@pytest.mark.django_db
class TestSyncAllCustomWellCO2Calculations:
    def test_should_sync_all_custom_well_co2_calculations(self, mock_sync_all_plan_co2_calculations_task: MagicMock):
        well = CustomWellFactory()
        plan_well_relation_1, plan_well_relation_2 = PlanWellRelationFactory.create_batch(2, well=well)
        PlanWellRelationFactory()

        result = sync_all_custom_well_co2_calculations_task.apply(args=(well.pk,))

        assert result.get() is None
        assert result.state == states.SUCCESS
        assert mock_sync_all_plan_co2_calculations_task.call_args_list == [
            call(plan_well_relation_1.plan.pk),
            call(plan_well_relation_2.plan.pk),
        ]

    def test_should_not_sync_all_custom_well_co2_calulations_for_draft_well(
        self, mock_sync_all_plan_co2_calculations_task: MagicMock
    ):
        well = CustomWellFactory(draft=True)
        PlanWellRelationFactory(well=well)

        result = sync_all_custom_well_co2_calculations_task.apply(args=(well.pk,))

        assert result.get() is None
        assert result.state == states.SUCCESS

        mock_sync_all_plan_co2_calculations_task.assert_not_called()


@pytest.mark.django_db
class TestSyncAllProjectCO2Calculations:
    def test_should_sync_all_project_co2_calculations(self, mock_sync_all_plan_co2_calculations_task: MagicMock):
        project = ProjectFactory()
        plan_1, plan_2 = PlanFactory.create_batch(2, project=project)
        PlanFactory()

        result = sync_all_project_co2_calculations_task.apply(args=(project.pk,))

        assert result.get() is None
        assert result.state == states.SUCCESS
        assert mock_sync_all_plan_co2_calculations_task.call_args_list == [
            call(plan_1.pk),
            call(plan_2.pk),
        ]
