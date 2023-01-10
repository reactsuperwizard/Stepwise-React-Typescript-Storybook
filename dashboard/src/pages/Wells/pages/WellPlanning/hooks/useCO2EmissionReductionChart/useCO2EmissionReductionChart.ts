import { useEmissionReduction } from 'pages/Wells/pages/WellPlanning/containers/EmissionReductionProvider';
import useCurrentWellPlan from 'pages/WellPlan/hooks/useCurrentWellPlan';
import useCO2EmissionReductions from 'pages/Wells/pages/WellPlanning/hooks/useCO2EmissionReductions';
import useLabels from 'pages/Wells/pages/WellPlanning/hooks/useLabels';
import useEmissionReductionInitiatives from 'pages/Wells/hooks/useEmissionReductionInitiatives';
import { ChartDataset } from 'chart.js';
import { notEmpty } from 'utils/data';
import { useMemo } from 'react';
import useEmissionReductionInitiativesColors from 'pages/WellPlan/hooks/useEmissionReductionInitiativesColors';

const useCO2EmissionReductionChart = () => {
  const [
    {
      xLegend,
      emissionReductionInitiatives: emissionReductionInitiativeFilters,
    },
  ] = useEmissionReduction();
  const { wellPlanId } = useCurrentWellPlan();
  const { powerSystems, baseloads } =
    useEmissionReductionInitiatives(wellPlanId);
  const {
    data: co2EmissionReductionData,
    isFetching: isFetchingCO2EmissionReduction,
  } = useCO2EmissionReductions(wellPlanId);
  const labels = useLabels(co2EmissionReductionData || [], xLegend);
  const { getEmissionReductionInitiativeColor } =
    useEmissionReductionInitiativesColors(wellPlanId);
  const emissionReductionInitiativeDatasets: ChartDataset<'bar'>[] = useMemo(
    () =>
      [...powerSystems, ...baseloads]
        .map((emissionReductionInitiative) => {
          return emissionReductionInitiativeFilters[
            emissionReductionInitiative.id
          ]
            ? {
                label: emissionReductionInitiative.name,
                data: (co2EmissionReductionData || []).map(
                  (co2EmissionReduction) =>
                    co2EmissionReduction.emission_reduction_initiatives.find(
                      (co2EmissionReductionInitiative) =>
                        co2EmissionReductionInitiative.id ===
                        emissionReductionInitiative.id,
                    )?.value || 0,
                ),
                backgroundColor: getEmissionReductionInitiativeColor(
                  emissionReductionInitiative,
                ),
                type: 'bar' as const,
              }
            : null;
        })
        .filter(notEmpty),
    [
      baseloads,
      co2EmissionReductionData,
      emissionReductionInitiativeFilters,
      getEmissionReductionInitiativeColor,
      powerSystems,
    ],
  );

  return {
    labels,
    datasets: emissionReductionInitiativeDatasets,
    isFetching: isFetchingCO2EmissionReduction,
  };
};

export default useCO2EmissionReductionChart;
