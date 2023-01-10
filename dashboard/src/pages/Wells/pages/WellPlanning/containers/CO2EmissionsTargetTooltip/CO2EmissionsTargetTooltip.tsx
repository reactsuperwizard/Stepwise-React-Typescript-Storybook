import { memo } from 'react';
import useTargetCO2Emissions from 'pages/Wells/pages/WellPlanning/hooks/useTargetCO2Emissions';
import EmissionsTargetTooltip from '../EmissionsTargetTooltip';

export interface CO2EmissionsTargetTooltipProps {
  dataIndex: number;
  xOverflow: boolean;
  wellPlanId: number;
  scopes: {
    scope1: boolean;
    scope2: boolean;
    scope3: boolean;
  };
}

const CO2EmissionsTargetTooltip = ({
  dataIndex,
  xOverflow,
  wellPlanId,
  scopes,
}: CO2EmissionsTargetTooltipProps) => {
  const { data: targetCO2Data } = useTargetCO2Emissions(wellPlanId);
  const data = (targetCO2Data || [])[dataIndex];
  if (!data) {
    return null;
  }
  return (
    <EmissionsTargetTooltip
      xOverflow={xOverflow}
      data={data}
      unit={
        <>
          CO<sub>2</sub> (Te)
        </>
      }
      scopes={scopes}
    />
  );
};

export default memo(CO2EmissionsTargetTooltip);
