import pytest

from apps.emissions.factories import (
    AssetFactory,
    BaselineFactory,
    BaselineInputFactory,
    CustomModeFactory,
    CustomPhaseFactory,
    EmissionManagementPlanFactory,
    EmissionReductionInitiativeFactory,
    EmissionReductionInitiativeInputFactory,
)
from apps.emissions.models import AssetSeason
from apps.emissions.serializers import (
    AssetDetailsSerializer,
    BaselineDetailsSerializer,
    EmissionManagementPlanDetailsSerializer,
    EmissionReductionInitiativeDetailsSerializer,
)


@pytest.mark.django_db
class TestAssetDetailsSerializer:
    def test_serialize_asset(self):
        asset = AssetFactory()

        serializer = AssetDetailsSerializer(asset)

        assert serializer.data['baselines'] == []
        assert serializer.data['emission_management_plans'] == []

    def test_serialize_asset_with_baselines(self):
        asset = AssetFactory()
        baseline = BaselineFactory(asset=asset, deleted=False)
        BaselineFactory(asset=asset, deleted=True)
        BaselineFactory(deleted=False)

        serializer = AssetDetailsSerializer(asset)

        assert serializer.data['baselines'] == [AssetDetailsSerializer.BaselineSerializer(baseline).data]
        assert serializer.data['emission_management_plans'] == []

    def test_serialize_asset_with_emission_management_plans(self):
        asset = AssetFactory()
        baseline = BaselineFactory(asset=asset, active=True)
        emission_management_plan = EmissionManagementPlanFactory(baseline=baseline)
        EmissionManagementPlanFactory(baseline__asset=asset)
        EmissionManagementPlanFactory()

        serializer = AssetDetailsSerializer(asset)

        assert serializer.data['emission_management_plans'] == [
            AssetDetailsSerializer.EmissionManagementPlanSerializer(emission_management_plan).data
        ]


@pytest.mark.django_db
class TestEmissionManagementPlanDetailsSerializer:
    def test_should_serialize_emission_management_plan(self):
        emission_management_plan = EmissionManagementPlanFactory()

        serializer = EmissionManagementPlanDetailsSerializer(emission_management_plan)

        assert serializer.data['initiatives'] == []

    def test_should_serialize_emission_management_plan_with_emission_reduction_initatives(self):
        emission_management_plan = EmissionManagementPlanFactory()
        emission_reduction_initiative = EmissionReductionInitiativeFactory(
            emission_management_plan=emission_management_plan
        )
        EmissionReductionInitiativeFactory(emission_management_plan=emission_management_plan, deleted=True)

        serializer = EmissionManagementPlanDetailsSerializer(emission_management_plan)

        assert (
            serializer.data['initiatives']
            == EmissionManagementPlanDetailsSerializer.EmissionManagementPlanDetailsInitiativeSerializer(
                [emission_reduction_initiative], many=True
            ).data
        )


@pytest.mark.django_db
class TestEmissionReductionInitiativeDetailsSerializer:
    def test_should_serialize_transit(self):
        emission_reduction_initiative = EmissionReductionInitiativeFactory()
        emission_reduction_initiative_input = EmissionReductionInitiativeInputFactory(
            emission_reduction_initiative=emission_reduction_initiative,
            phase__phase__transit=True,
            mode__mode__transit=True,
            value=999.99,
        )
        serializer = EmissionReductionInitiativeDetailsSerializer(emission_reduction_initiative)

        assert serializer.data['transit'] == emission_reduction_initiative_input.value

    def test_should_return_0_for_non_existing_transit(self):
        emission_reduction_initiative = EmissionReductionInitiativeFactory()
        serializer = EmissionReductionInitiativeDetailsSerializer(emission_reduction_initiative)

        assert serializer.data['transit'] == 0


@pytest.mark.django_db
class TestBaselineDetailsSerializer:
    def test_should_serialize_baseline(self):
        baseline = BaselineFactory()

        transit_phase = CustomPhaseFactory(
            asset=baseline.asset,
            phase__transit=True,
        )
        transit_mode = CustomModeFactory(
            asset=baseline.asset,
            mode__transit=True,
        )
        phase = CustomPhaseFactory(asset=baseline.asset)
        mode = CustomModeFactory(asset=baseline.asset)

        baseline_summer_transit_input = BaselineInputFactory(
            baseline=baseline,
            season=AssetSeason.SUMMER,
            phase=transit_phase,
            mode=transit_mode,
            value=999.99,
        )
        baseline_winter_transit_input = BaselineInputFactory(
            baseline=baseline,
            phase=transit_phase,
            mode=transit_mode,
            season=AssetSeason.WINTER,
            value=888.88,
        )
        baseline_summer_input = BaselineInputFactory(
            baseline=baseline,
            phase=phase,
            mode=mode,
            season=AssetSeason.SUMMER,
            value=777.77,
        )
        baseline_winter_input = BaselineInputFactory(
            baseline=baseline,
            phase=phase,
            mode=mode,
            season=AssetSeason.WINTER,
            value=666.66,
        )

        serializer = BaselineDetailsSerializer(baseline)

        assert serializer.data['winter'] == {
            'transit': baseline_winter_transit_input.value,
            'inputs': BaselineDetailsSerializer.BaselineDetailsSeasonSerializer.BaselineDetailsInputSerializer(
                [baseline_winter_input], many=True
            ).data,
        }
        assert serializer.data['summer'] == {
            'transit': baseline_summer_transit_input.value,
            'inputs': BaselineDetailsSerializer.BaselineDetailsSeasonSerializer.BaselineDetailsInputSerializer(
                [baseline_summer_input], many=True
            ).data,
        }
