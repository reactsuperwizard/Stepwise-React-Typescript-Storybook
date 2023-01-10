import pytest

from apps.projects.models import ElementType
from apps.rigs.factories import (
    CustomDrillshipFactory,
    CustomJackupRigFactory,
    CustomJackupSubareaScoreFactory,
    CustomSemiRigFactory,
    CustomSemiSubareaScoreFactory,
)
from apps.rigs.models import (
    CustomDrillship,
    CustomJackupRig,
    CustomJackupSubareaScore,
    CustomSemiRig,
    CustomSemiSubareaScore,
    RigType,
)


@pytest.mark.django_db
class TestCustomRigQuerySet:
    @pytest.mark.parametrize(
        'RigModel, RigFactory, type',
        (
            (CustomDrillship, CustomDrillshipFactory, RigType.DRILLSHIP),
            (CustomSemiRig, CustomSemiRigFactory, RigType.SEMI),
            (CustomJackupRig, CustomJackupRigFactory, RigType.JACKUP),
        ),
    )
    def test_with_type(self, RigModel, RigFactory, type):
        rig = RigFactory()

        assert RigModel.objects.with_type().get(pk=rig.pk).type == type

    @pytest.mark.parametrize(
        'RigModel, RigFactory, element_type',
        (
            (CustomDrillship, CustomDrillshipFactory, ElementType.DRILLSHIP),
            (CustomSemiRig, CustomSemiRigFactory, ElementType.SEMI_RIG),
            (CustomJackupRig, CustomJackupRigFactory, ElementType.JACKUP_RIG),
        ),
    )
    def test_with_element_type(self, RigModel, RigFactory, element_type):
        rig = RigFactory()

        assert RigModel.objects.with_element_type().get(pk=rig.pk).element_type == element_type


@pytest.mark.django_db
class TestCustomJackupSubareaScore:
    def test_efficiency(self):
        subarea_score = CustomJackupSubareaScoreFactory(
            rig_status=0.12,
            topside_efficiency=0.21,
            deck_efficiency=0.33,
            move_and_installation=0.47,
            capacities=0.58,
            co2=0.67,
        )
        assert subarea_score.efficiency == 0.34199999999999997


@pytest.mark.django_db
class TestCustomJackupSubareaScoreManager:
    def test_get_or_calculate(self, concept_cj70):
        assert CustomJackupSubareaScore.objects.filter(rig=concept_cj70).exists() is False

        subarea_score = CustomJackupSubareaScore.objects.get_or_calculate(concept_cj70)

        assert concept_cj70.subarea_score == subarea_score


@pytest.mark.django_db
class TestCustomSemiSubareaScore:
    def test_efficiency(self):
        subarea_score = CustomSemiSubareaScoreFactory(
            rig_status=0.12,
            topside_efficiency=0.21,
            deck_efficiency=0.33,
            wow=0.47,
            capacities=0.58,
            co2=0.67,
        )
        assert subarea_score.efficiency == 0.34199999999999997


@pytest.mark.django_db
class TestCustomSemiSubareaScoreManager:
    def test_get_or_calculate(self, concept_cs60):
        assert CustomSemiSubareaScore.objects.filter(rig=concept_cs60).exists() is False

        subarea_score = CustomSemiSubareaScore.objects.get_or_calculate(concept_cs60)

        assert concept_cs60.subarea_score == subarea_score
