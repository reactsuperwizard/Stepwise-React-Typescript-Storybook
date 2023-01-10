import { useCallback, useMemo } from 'react';
import useEmissionReductionInitiatives from 'pages/Wells/hooks/useEmissionReductionInitiatives';
import { useTheme } from 'styled-components';
import {
  EmissionReductionInitiativeList,
  EmissionReductionInitiativeTypeEnum,
} from 'api/schema';

const mapColors = <
  Colors extends Record<
    '1' | '2' | '3' | '4' | '5' | '6' | '7' | '8' | '9' | '10',
    string
  >,
>(
  data: EmissionReductionInitiativeList[],
  colors: Colors,
) => {
  return data.reduce<Record<string, string>>(
    (previousValue, currentValue, currentIndex) => {
      previousValue[currentValue.id] = String(
        colors[((currentIndex % 10) + 1) as keyof Colors],
      );
      return previousValue;
    },
    {},
  );
};

const useEmissionReductionInitiativesColors = (wellPlanId: number) => {
  const { powerSystems, baseloads, productivity } =
    useEmissionReductionInitiatives(wellPlanId);
  const { colors } = useTheme();
  const powerSystemsColors = useMemo(
    () => mapColors(powerSystems, colors.salomn),
    [colors, powerSystems],
  );
  const baseloadsColors = useMemo(
    () => mapColors(baseloads, colors.turquoise),
    [colors, baseloads],
  );
  const productivityColors = useMemo(
    () => mapColors(productivity, colors.sunset),
    [colors, productivity],
  );
  const getEmissionReductionInitiativeColor = useCallback(
    (emissionReductionInitiative: EmissionReductionInitiativeList) => {
      switch (emissionReductionInitiative.type) {
        case EmissionReductionInitiativeTypeEnum.BASELOADS:
          return baseloadsColors[emissionReductionInitiative.id];
        case EmissionReductionInitiativeTypeEnum.PRODUCTIVITY:
          return productivityColors[emissionReductionInitiative.id];
        case EmissionReductionInitiativeTypeEnum.POWER_SYSTEMS:
          return powerSystemsColors[emissionReductionInitiative.id];
        default:
          throw new Error(
            `Unknown emission reductio initiative type: ${emissionReductionInitiative.type}`,
          );
      }
    },
    [baseloadsColors, powerSystemsColors, productivityColors],
  );

  return {
    getEmissionReductionInitiativeColor,
  };
};

export default useEmissionReductionInitiativesColors;
