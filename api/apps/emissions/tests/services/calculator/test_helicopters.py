import pytest
from django.db.models import QuerySet

from apps.emissions.factories import PlannedHelicopterUseFactory
from apps.emissions.models import PlannedHelicopterUse
from apps.emissions.services.calculator.helicopters import (
    calculate_helicopter_co2,
    calculate_helicopter_fuel,
    calculate_helicopter_nox,
    calculate_step_helicopters_co2,
    calculate_step_helicopters_fuel,
    calculate_step_helicopters_nox,
)

# v20.12.22
HELICOPTERS = {
    'Sikorsky S-92': dict(
        # 'Well Planning'!O19
        roundtrip_minutes=90,
        # 'Well Planning'!P19
        roundtrip_count=8,
        # 'Asset & Materials Input'!F86
        fuel_consumption=641,
        # 'Well Planning'!Q19
        exposure=50,
        # 'Asset & Materials Input'!G86
        co2_per_fuel=3.15,
        # 'Asset & Materials Input'!H86
        fuel_density=800.0,
        # 'Asset & Materials Input'!I86
        nox_per_fuel=53.5,
    ),
    'Super Puma': dict(
        # 'Well Planning'!O20
        roundtrip_minutes=91,
        # 'Well Planning'!P20
        roundtrip_count=9,
        # 'Asset & Materials Input'!F87
        fuel_consumption=650,
        # 'Well Planning'!Q20
        exposure=100,
        # 'Asset & Materials Input'!G87
        co2_per_fuel=3.15,
        # 'Asset & Materials Input'!H87
        fuel_density=800.0,
        # 'Asset & Materials Input'!I87
        nox_per_fuel=53.5,
    ),
}


@pytest.fixture
def helicopter_uses() -> QuerySet[PlannedHelicopterUse]:
    for helicopter in HELICOPTERS.values():
        PlannedHelicopterUseFactory(
            trips=helicopter['roundtrip_count'],
            trip_duration=helicopter['roundtrip_minutes'],
            exposure_against_current_well=helicopter['exposure'],
            helicopter_type__fuel_consumption=helicopter['fuel_consumption'],
            helicopter_type__co2_per_fuel=helicopter['co2_per_fuel'],
            helicopter_type__fuel_density=helicopter['fuel_density'],
            helicopter_type__nox_per_fuel=helicopter['nox_per_fuel'],
        )

    return PlannedHelicopterUse.objects.all()


# v20.12.22
@pytest.mark.django_db
@pytest.mark.parametrize(
    'helicopter,expected',
    (
        # 'Calculation'!F98
        ('Sikorsky S-92', 3.846),
        # 'Calculation'!F99
        ('Super Puma', 8.872499999999999),
    ),
)
def test_calculate_helicopter_fuel(
    helicopter: str,
    expected: float,
):
    assert (
        calculate_helicopter_fuel(
            roundtrip_minutes=HELICOPTERS[helicopter]['roundtrip_minutes'],
            roundtrip_count=HELICOPTERS[helicopter]['roundtrip_count'],
            fuel_consumption=HELICOPTERS[helicopter]['fuel_consumption'],
            exposure=HELICOPTERS[helicopter]['exposure'],
        )
        == expected
    )


# v20.12.22
@pytest.mark.django_db
@pytest.mark.parametrize(
    'helicopter_name,expected',
    (
        # 'Calculation'!H98
        ('Sikorsky S-92', 12.1149),
        # 'Calculation'!H99
        ('Super Puma', 27.948374999999995),
    ),
)
def test_calculate_helicopter_co2(
    helicopter_name: str,
    expected: float,
):
    assert (
        calculate_helicopter_co2(
            roundtrip_minutes=HELICOPTERS[helicopter_name]['roundtrip_minutes'],
            roundtrip_count=HELICOPTERS[helicopter_name]['roundtrip_count'],
            fuel_consumption=HELICOPTERS[helicopter_name]['fuel_consumption'],
            exposure=HELICOPTERS[helicopter_name]['exposure'],
            co2_per_fuel=HELICOPTERS[helicopter_name]['co2_per_fuel'],
        )
        == expected
    )


# v20.12.22
@pytest.mark.django_db
@pytest.mark.parametrize(
    'helicopter_name,expected',
    (
        # 'Calculation'!I98
        ("Sikorsky S-92", 0.16460880000000003),
        # 'Calculation'!I99
        ("Super Puma", 0.37974299999999994),
    ),
)
def test_calculate_helicopter_nox(
    helicopter_name: str,
    expected: str,
):
    assert (
        calculate_helicopter_nox(
            roundtrip_minutes=HELICOPTERS[helicopter_name]['roundtrip_minutes'],
            roundtrip_count=HELICOPTERS[helicopter_name]['roundtrip_count'],
            fuel_consumption=HELICOPTERS[helicopter_name]['fuel_consumption'],
            exposure=HELICOPTERS[helicopter_name]['exposure'],
            fuel_density=HELICOPTERS[helicopter_name]['fuel_density'],
            nox_per_fuel=HELICOPTERS[helicopter_name]['nox_per_fuel'],
        )
        == expected
    )


# v20.12.22
@pytest.mark.django_db
def test_calculate_step_helicopters_fuel(
    helicopter_uses: QuerySet[HELICOPTERS],
):
    assert (
        calculate_step_helicopters_fuel(
            helicopter_uses=helicopter_uses,
            # 'Well Planning'!J54
            step_duration=9.56,
            # 'Well Planning'!G68
            plan_duration=18.58,
        )
        # 'Calculation'!F107
        == 6.544072120559742
    )


# v20.12.22
@pytest.mark.django_db
def test_calculate_step_helicopters_co2(
    helicopter_uses: QuerySet[HELICOPTERS],
):
    assert (
        calculate_step_helicopters_co2(
            helicopter_uses=helicopter_uses,
            # 'Well Planning'!J54
            step_duration=9.56,
            # 'Well Planning'!G68
            plan_duration=18.58,
        )
        # 'Calculation'!H107
        == 20.613827179763184
    )


# v20.12.22
@pytest.mark.django_db
def test_calculate_step_helicopters_nox(
    helicopter_uses: QuerySet[HELICOPTERS],
):
    assert (
        calculate_step_helicopters_nox(
            helicopter_uses=helicopter_uses,
            # 'Well Planning'!J54
            step_duration=9.56,
            # 'Well Planning'!G68
            plan_duration=18.58,
        )
        # 'Calculation'!I107
        == 0.280086286759957
    )
