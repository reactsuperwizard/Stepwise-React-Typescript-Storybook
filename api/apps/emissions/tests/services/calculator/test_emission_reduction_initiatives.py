import pytest

from apps.emissions.factories.assets import EmissionReductionInitiativeInputFactory
from apps.emissions.services.calculator.emission_reduction_initiatives import (
    InitiativeReductionData,
    calculate_emission_reduction_initiative_reductions,
    calculate_step_emission_reduction_initiative_reductions,
    calculate_total_emission_reduction_initiative_reduction,
)
from apps.wells.factories import WellPlannerPlannedStepFactory

# v20.12.2022
INITIATIVES = {
    "Power System ERI": InitiativeReductionData(
        emission_reduction_initiative_id=1,
        # 'Calculation'!F180
        value=9.0,
    ),
    "Base loads ERI": InitiativeReductionData(
        emission_reduction_initiative_id=2,
        # 'Calculation'!F188
        value=8.0,
    ),
}


# v20.12.2022
@pytest.mark.django_db
def test_calculate_emission_reduction_initiative_reductions():
    assert calculate_emission_reduction_initiative_reductions(
        # 'Calculation'!E7
        baseline=789.5,
        initiatives=INITIATIVES.values(),
    ) == [
        InitiativeReductionData(
            emission_reduction_initiative_id=1,
            # 'Calculation'!G180
            value=71.055,
        ),
        InitiativeReductionData(
            emission_reduction_initiative_id=2,
            # 'Calculation'!G188
            value=63.16,
        ),
    ]


# v20.12.2022
@pytest.mark.django_db
def test_calculate_step_emission_reduction_initiative_reductions():
    step = WellPlannerPlannedStepFactory()

    first_initiative_input, second_initiative_input = (
        EmissionReductionInitiativeInputFactory(
            phase=step.phase,
            mode=step.mode,
            value=initiative['value'],
        )
        for initiative in INITIATIVES.values()
    )

    step.emission_reduction_initiatives.add(
        first_initiative_input.emission_reduction_initiative, second_initiative_input.emission_reduction_initiative
    )

    assert calculate_step_emission_reduction_initiative_reductions(
        # 'Calculation'!E7
        baseline=789.5,
        step=step,
    ) == [
        InitiativeReductionData(
            emission_reduction_initiative_id=first_initiative_input.emission_reduction_initiative_id,
            # 'Calculation'!G180
            value=71.055,
        ),
        InitiativeReductionData(
            emission_reduction_initiative_id=second_initiative_input.emission_reduction_initiative_id,
            # 'Calculation'!G188
            value=63.16,
        ),
    ]


# v20.12.2022
@pytest.mark.django_db
def test_calculate_total_step_emission_reduction_initiative_reductions():
    assert (
        calculate_total_emission_reduction_initiative_reduction(
            initiatives=[
                InitiativeReductionData(
                    emission_reduction_initiative_id=1,
                    value=100,
                ),
                InitiativeReductionData(
                    emission_reduction_initiative_id=2,
                    value=200,
                ),
                InitiativeReductionData(
                    emission_reduction_initiative_id=3,
                    value=300,
                ),
            ]
        )
        == 600
    )
