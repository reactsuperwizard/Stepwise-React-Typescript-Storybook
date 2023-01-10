import { Flexbox } from 'components/Box';
import ChartToggle from 'pages/WellPlan/components/ChartToggle';
import { useEmissionsTarget } from 'pages/Wells/pages/WellPlanning/containers/EmissionsTargetProvider';
import { useTheme } from 'styled-components';
import { useMemo } from 'react';
import { MeasuredValue } from 'pages/Wells/consts';

const EmissionsTargetFilters = () => {
  const [
    {
      value,
      lines: { baseline, target },
      scopes: { scope1, scope2, scope3 },
    },
    dispatch,
  ] = useEmissionsTarget();
  const { colors } = useTheme();
  const isLastActiveScope = useMemo(() => {
    if ([MeasuredValue.FuelCost, MeasuredValue.Fuel].includes(value)) {
      return [scope1, scope3].filter(Boolean).length === 1;
    }
    return [scope1, scope2, scope3].filter(Boolean).length === 1;
  }, [scope1, scope2, scope3, value]);

  return (
    <Flexbox justifyContent="space-between">
      <Flexbox gap={1} marginRight={40}>
        <ChartToggle
          label="Baseline"
          type="line"
          enabled={baseline}
          color={colors.blue['6']}
          onClick={() =>
            dispatch({
              type: 'toggleLine',
              line: 'baseline',
            })
          }
        />
        <ChartToggle
          label="Target"
          type="line"
          enabled={target}
          color={colors.salomn['1']}
          onClick={() =>
            dispatch({
              type: 'toggleLine',
              line: 'target',
            })
          }
        />
      </Flexbox>
      <Flexbox gap={1} flexWrap="wrap" justifyContent="flex-end">
        <ChartToggle
          label="Scope 1"
          type="circle"
          disabled={scope1 && isLastActiveScope}
          enabled={scope1}
          color={colors.netZeroBlue['3']}
          onClick={() =>
            dispatch({
              type: 'toggleScope',
              scope: 'scope1',
            })
          }
        />
        <ChartToggle
          label="Scope 2"
          type="circle"
          enabled={scope2}
          disabled={
            (scope2 && isLastActiveScope) ||
            [MeasuredValue.Fuel, MeasuredValue.FuelCost].includes(value)
          }
          color={colors.netZeroBlue['6']}
          onClick={() =>
            dispatch({
              type: 'toggleScope',
              scope: 'scope2',
            })
          }
        />
        <ChartToggle
          label="Scope 3"
          type="circle"
          enabled={scope3}
          disabled={scope3 && isLastActiveScope}
          color={colors.netZeroBlue['9']}
          onClick={() =>
            dispatch({
              type: 'toggleScope',
              scope: 'scope3',
            })
          }
        />
      </Flexbox>
    </Flexbox>
  );
};

export default EmissionsTargetFilters;
