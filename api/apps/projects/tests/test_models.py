import pytest

from apps.rigs.factories import CustomDrillshipFactory, CustomJackupRigFactory, CustomSemiRigFactory
from apps.rigs.models import CustomDrillship, CustomJackupRig, CustomSemiRig


@pytest.mark.django_db
class TestCustomJackupRigQuerySet:
    def test_studiable(self):
        CustomJackupRigFactory()

        assert CustomJackupRig.objects.studiable().count() == 1


@pytest.mark.django_db
class TestCustomSemiRigQuerySet:
    def test_studiable(self):
        dp = CustomSemiRigFactory(dp=True)
        ata = CustomSemiRigFactory(thruster_assist=True)
        CustomSemiRigFactory(dp=False, thruster_assist=False)

        assert list(CustomSemiRig.objects.studiable().order_by('id')) == [dp, ata]


@pytest.mark.django_db
class TestCustomDrillshipQuerySet:
    def test_studiable(self):
        CustomDrillshipFactory()

        assert CustomDrillship.objects.studiable().count() == 0
