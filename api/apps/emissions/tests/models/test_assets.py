from typing import Callable

import pytest

from apps.emissions.factories import BaselineFactory, EmissionReductionInitiativeFactory
from apps.emissions.factories.assets import CustomModeFactory, CustomPhaseFactory
from apps.wells.factories import WellPlannerFactory


@pytest.mark.django_db
class TestBaselineIsUsed:
    def test_should_be_false_for_unused_baseline(self):
        baseline = BaselineFactory()
        WellPlannerFactory(baseline=baseline, deleted=True)
        WellPlannerFactory()
        EmissionReductionInitiativeFactory()
        EmissionReductionInitiativeFactory(emission_management_plan__baseline=baseline, deleted=True)

        assert baseline.is_used is False

    def test_should_be_true_for_baseline_used_by_well_plan(self):
        baseline = BaselineFactory()
        WellPlannerFactory(baseline=baseline)

        assert baseline.is_used is True

    def test_should_be_true_for_baseline_used_by_emission_reduction_initiative(self):
        baseline = BaselineFactory()
        EmissionReductionInitiativeFactory(emission_management_plan__baseline=baseline)

        assert baseline.is_used is True


@pytest.mark.django_db
class TestCustomModeTransit:
    @pytest.mark.parametrize(
        "Factory,expected_transit",
        (
            (lambda: CustomModeFactory(mode__transit=False), False),
            (lambda: CustomModeFactory(mode__transit=True), True),
            (lambda: CustomModeFactory(mode=None), False),
        ),
    )
    def test_custom_mode_transit(self, Factory: Callable, expected_transit: bool):
        custom_mode = Factory()
        assert custom_mode.transit is expected_transit


@pytest.mark.django_db
class TestCustomPhaseTransit:
    @pytest.mark.parametrize(
        "Factory,expected_transit",
        (
            (lambda: CustomPhaseFactory(phase__transit=False), False),
            (lambda: CustomPhaseFactory(phase__transit=True), True),
            (lambda: CustomPhaseFactory(phase=None), False),
        ),
    )
    def test_custom_phase_transit(self, Factory: Callable, expected_transit: bool):
        custom_phase = Factory()
        assert custom_phase.transit is expected_transit
