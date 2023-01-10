import { memo } from 'react';
import theme from 'style/theme';
import {
  Tooltip,
  TooltipHeader,
  TooltipTotal,
  TooltipItem,
} from 'pages/Wells/pages/WellPlanning/components/ContributionTooltip';
import { WellCO2Emission } from 'api/schema';
import { calculateTotalCO2Emission } from 'pages/Wells/pages/WellPlanning/utils/calc';

interface EmissionsTargetTooltipProps {
  data: WellCO2Emission;
  unit: React.ReactNode;
  xOverflow: boolean;
  scopes: {
    scope1: boolean;
    scope2: boolean;
    scope3: boolean;
  };
}

const EmissionsTargetTooltip = ({
  scopes,
  unit,
  data,
  xOverflow,
}: EmissionsTargetTooltipProps) => {
  const { scope1, scope2, scope3 } = scopes;
  const total = calculateTotalCO2Emission({
    scopes,
    data,
  });

  return (
    <Tooltip xOverflow={xOverflow} width={200}>
      {scope1 ? (
        <>
          <TooltipHeader
            color={theme.colors.netZeroBlue[3]}
            title="Scope 1 emissions"
          />
          <TooltipItem title="Drilling asset" value={data.asset} unit={unit} />
          <TooltipItem title="Boilers" value={data.boilers} unit={unit} />
        </>
      ) : null}
      {scope2 ? (
        <>
          <TooltipHeader
            color={theme.colors.netZeroBlue[6]}
            title="Scope 2 emissions"
          />
          <TooltipItem
            title="External power supply"
            value={data.external_energy_supply}
            unit={unit}
          />
        </>
      ) : null}
      {scope3 ? (
        <>
          <TooltipHeader
            color={theme.colors.netZeroBlue[9]}
            title="Scope 3 emissions"
          />
          <TooltipItem title="Vessels" value={data.vessels} unit={unit} />
          <TooltipItem
            title="Helicopters"
            value={data.helicopters}
            unit={unit}
          />
          <TooltipItem title="Materials" value={data.materials} unit={unit} />
        </>
      ) : null}
      <TooltipTotal value={total} unit={unit} />
    </Tooltip>
  );
};

export default memo(EmissionsTargetTooltip);
