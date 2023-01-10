import pytest
from django.db.models import QuerySet

from apps.emissions.factories import WellPlannedStepMaterialFactory
from apps.emissions.models import WellPlannedStepMaterial
from apps.emissions.services.calculator.materials import calculate_material_co2, calculate_step_materials_co2

MATERIALS = {
    'STEEL': dict(
        # 'Well Planning'!N54
        quantity=10,
        # 'Well Planning'!I31
        co2_per_unit=6,
    ),
    'CEMENT': dict(
        # 'Well Planning'!O54
        quantity=14,
        # 'Well Planning'!I32
        co2_per_unit=6,
    ),
    'BULK': dict(
        # 'Well Planning'!P54
        quantity=5,
        # 'Well Planning'!I33
        co2_per_unit=15,
    ),
    'CHEMICALS': dict(
        # 'Well Planning'!Q54
        quantity=20,
        # 'Well Planning'!I34
        co2_per_unit=5,
    ),
}


@pytest.fixture
def materials() -> QuerySet[WellPlannedStepMaterial]:
    for material in MATERIALS.values():
        WellPlannedStepMaterialFactory(
            quantity=material['quantity'],
            material_type__co2=material['co2_per_unit'],
        )

    return WellPlannedStepMaterial.objects.all()


# v20.12.22
@pytest.mark.django_db
@pytest.mark.parametrize(
    'material,expected',
    (
        ('STEEL', 60),
        ('CEMENT', 84),
        ('BULK', 75),
        ('CHEMICALS', 100),
    ),
)
def test_calculate_material_co2(material: str, expected: float):
    assert (
        calculate_material_co2(
            quantity=MATERIALS[material]['quantity'],
            co2_per_unit=MATERIALS[material]['co2_per_unit'],
        )
        == expected
    )


# v20.12.22
@pytest.mark.django_db
def test_calculate_step_materials_co2(materials: QuerySet[WellPlannedStepMaterial]):
    assert calculate_step_materials_co2(materials=materials) == 319
