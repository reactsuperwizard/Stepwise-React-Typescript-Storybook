import useCO2EmissionReductions from 'pages/Wells/pages/WellPlanning/hooks/useCO2EmissionReductions';
import EmissionReductionTooltip from '../EmissionReductionTooltip';

export interface CO2EmissionReductionTooltipProps {
  dataIndex: number;
  xOverflow: boolean;
  wellPlanId: number;
  emissionReductionInitiativeFilters: Record<string, boolean>;
}

const CO2EmissionReductionTooltip = ({
  emissionReductionInitiativeFilters,
  xOverflow,
  wellPlanId,
  dataIndex,
}: CO2EmissionReductionTooltipProps) => {
  const { data: co2EmissionReductionsData } =
    useCO2EmissionReductions(wellPlanId);
  const data = (co2EmissionReductionsData || [])[dataIndex];
  if (!data) {
    return null;
  }
  return (
    <EmissionReductionTooltip
      xOverflow={xOverflow}
      data={data}
      wellPlanId={wellPlanId}
      unit={
        <>
          CO<sub>2</sub> (Te)
        </>
      }
      emissionReductionInitiativeFilters={emissionReductionInitiativeFilters}
    />
  );
};

export default CO2EmissionReductionTooltip;
