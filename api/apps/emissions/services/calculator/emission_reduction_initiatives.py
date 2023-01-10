from typing import TypedDict

from apps.emissions.models.assets import EmissionReductionInitiativeInput, EmissionReductionInitiativeType
from apps.wells.models import WellPlannerPlannedStep


class InitiativeReductionData(TypedDict):
    emission_reduction_initiative_id: int
    value: float


def calculate_emission_reduction_initiative_reductions(
    *,
    baseline: float,
    initiatives: list[InitiativeReductionData],
) -> list[InitiativeReductionData]:
    return [
        InitiativeReductionData(
            emission_reduction_initiative_id=initiative["emission_reduction_initiative_id"],
            value=baseline * initiative["value"] / 100,
        )
        for initiative in initiatives
    ]


def calculate_total_emission_reduction_initiative_reduction(
    *,
    initiatives: list[InitiativeReductionData],
) -> float:
    return sum(initiative['value'] for initiative in initiatives)


def calculate_step_emission_reduction_initiative_reductions(
    *,
    baseline: float,
    step: WellPlannerPlannedStep,
) -> list[InitiativeReductionData]:
    emission_reduction_initiative_inputs = EmissionReductionInitiativeInput.objects.filter(
        emission_reduction_initiative__in=step.emission_reduction_initiatives.exclude(
            type=EmissionReductionInitiativeType.PRODUCTIVITY
        ),
        phase=step.phase,
        mode=step.mode,
    ).order_by('id')

    return calculate_emission_reduction_initiative_reductions(
        baseline=baseline,
        initiatives=[
            InitiativeReductionData(
                emission_reduction_initiative_id=initiative_input.emission_reduction_initiative_id,
                value=initiative_input.value,
            )
            for initiative_input in emission_reduction_initiative_inputs
        ],
    )
