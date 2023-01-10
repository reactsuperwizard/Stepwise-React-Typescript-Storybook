import { memo } from 'react';
import {
  Tooltip,
  TooltipHeader,
  TooltipTotal,
  TooltipItem,
} from 'pages/Wells/pages/WellPlanning/components/ContributionTooltip';
import {
  EmissionReductionInitiative,
  EmissionReductionInitiativeTypeEnum,
  WellEmissionReduction,
} from 'api/schema';
import { sumValues } from 'utils/math';
import useEmissionReductionInitiativesColors from 'pages/WellPlan/hooks/useEmissionReductionInitiativesColors';

interface EmissionReductionTooltipProps {
  wellPlanId: number;
  data: WellEmissionReduction;
  unit: React.ReactNode;
  xOverflow: boolean;
  emissionReductionInitiativeFilters: Record<string, boolean>;
}

const filterEmissionReductionInitiatives = ({
  emissionReductionInitiatives,
  type,
  emissionReductionInitiativeFilters,
}: {
  emissionReductionInitiatives: EmissionReductionInitiative[];
  type: EmissionReductionInitiativeTypeEnum;
  emissionReductionInitiativeFilters: Record<string, boolean>;
}) => {
  return emissionReductionInitiatives.filter(
    (emissionReductionInitiative) =>
      emissionReductionInitiative.type === type &&
      emissionReductionInitiativeFilters[emissionReductionInitiative.id],
  );
};

const EmissionReductionTooltip = ({
  emissionReductionInitiativeFilters,
  unit,
  data,
  xOverflow,
  wellPlanId,
}: EmissionReductionTooltipProps) => {
  const { getEmissionReductionInitiativeColor } =
    useEmissionReductionInitiativesColors(wellPlanId);
  const powerSystems = filterEmissionReductionInitiatives({
    emissionReductionInitiatives: data.emission_reduction_initiatives,
    type: EmissionReductionInitiativeTypeEnum.POWER_SYSTEMS,
    emissionReductionInitiativeFilters,
  });
  const baseloads = filterEmissionReductionInitiatives({
    emissionReductionInitiatives: data.emission_reduction_initiatives,
    type: EmissionReductionInitiativeTypeEnum.BASELOADS,
    emissionReductionInitiativeFilters,
  });
  const total = sumValues(
    powerSystems
      .concat(baseloads)
      .map((emissionReductionInitiative) => emissionReductionInitiative.value),
  );

  if (!baseloads.length && !powerSystems.length) {
    return null;
  }

  return (
    <Tooltip xOverflow={xOverflow} width={267}>
      {powerSystems.length ? (
        <>
          <TooltipHeader title="Power systems" />
          {powerSystems.map((powerSystem) => (
            <TooltipItem
              title={powerSystem.name}
              value={-powerSystem.value}
              color={getEmissionReductionInitiativeColor(powerSystem)}
              unit={unit}
            />
          ))}
        </>
      ) : null}
      {baseloads.length ? (
        <>
          <TooltipHeader title="Baseloads" />
          {baseloads.map((baseload) => (
            <TooltipItem
              title={baseload.name}
              value={-baseload.value}
              color={getEmissionReductionInitiativeColor(baseload)}
              unit={unit}
            />
          ))}
        </>
      ) : null}
      <TooltipTotal value={-total} unit={unit} />
    </Tooltip>
  );
};

export default memo(EmissionReductionTooltip);
