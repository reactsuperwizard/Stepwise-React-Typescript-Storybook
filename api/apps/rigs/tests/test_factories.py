import pytest

from apps.rigs.factories import ConceptJackupRigFactory, ConceptSemiRigFactory


@pytest.mark.django_db
class TestConceptSemiRigFactory:
    def test_factory(self):
        ConceptSemiRigFactory()


@pytest.mark.django_db
class TestConceptJackupRigFactory:
    def test_factory(self):
        ConceptJackupRigFactory()
