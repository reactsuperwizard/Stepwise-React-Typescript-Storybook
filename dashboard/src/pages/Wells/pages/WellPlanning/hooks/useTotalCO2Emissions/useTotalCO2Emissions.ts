import { WellCO2Emission } from 'api/schema';
import useBaselineCO2Emissions from 'pages/Wells/pages/WellPlanning/hooks/useBaselineCO2Emissions';
import useTargetCO2Emissions from 'pages/Wells/pages/WellPlanning/hooks/useTargetCO2Emissions';
import { useCallback, useMemo } from 'react';

const useTotalCO2Emissions = (wellPlanId: number) => {
  const { data: baselineCO2Data } = useBaselineCO2Emissions(wellPlanId);
  const { data: targetCO2Data } = useTargetCO2Emissions(wellPlanId);
  const calculateTotalCO2 = useCallback(
    (previousValue: number, currentValue: WellCO2Emission) => {
      return (
        previousValue +
        (currentValue.asset +
          currentValue.boilers +
          currentValue.external_energy_supply +
          (currentValue.vessels +
            currentValue.helicopters +
            currentValue.materials))
      );
    },
    [],
  );

  const baseline = useMemo(
    () => (baselineCO2Data || []).reduce(calculateTotalCO2, 0),
    [baselineCO2Data, calculateTotalCO2],
  );
  const target = useMemo(
    () => (targetCO2Data || []).reduce(calculateTotalCO2, 0),
    [targetCO2Data, calculateTotalCO2],
  );

  return {
    baseline,
    target,
  };
};

export default useTotalCO2Emissions;
