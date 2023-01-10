import pytest

from apps.wells.factories import ConceptWellFactory


@pytest.mark.django_db
class TestConceptWellFactory:
    def test_factory(self):
        ConceptWellFactory()
