from django.db.models import QuerySet

from apps.emissions.models.wells import BaseWellStepMaterial


# v20.12.2022
# 'Calculation'!H142
def calculate_material_co2(
    *,
    # 'Well Planning'!N54
    quantity: float,
    # 'Well Planning'!I31
    co2_per_unit: float,
) -> float:
    return quantity * co2_per_unit


# v20.12.2022
def calculate_step_materials_co2(
    *,
    materials: QuerySet[BaseWellStepMaterial],
) -> float:
    return sum(
        calculate_material_co2(
            quantity=material.quantity,
            co2_per_unit=material.material_type.co2,
        )
        for material in materials
    )
