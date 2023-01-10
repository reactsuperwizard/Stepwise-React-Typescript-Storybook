import useCurrentWellPlan from 'pages/WellPlan/hooks/useCurrentWellPlan';
import useTotalCO2Emissions from 'pages/Wells/pages/WellPlanning/hooks/useTotalCO2Emissions';
import TotalEmissions from 'pages/Wells/pages/WellPlanning/components/TotalEmissions';

const TotalCO2EmissionsTarget = () => {
  const { wellPlanId } = useCurrentWellPlan();
  const { baseline, target } = useTotalCO2Emissions(wellPlanId);

  return (
    <TotalEmissions
      baseline={baseline}
      target={target}
      unit={
        <>
          CO
          <sub>2</sub> Te
        </>
      }
    />
  );
};

export default TotalCO2EmissionsTarget;
