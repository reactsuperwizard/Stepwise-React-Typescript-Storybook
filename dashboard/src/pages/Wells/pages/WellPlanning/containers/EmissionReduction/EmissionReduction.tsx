import ChartYScaleProvider from 'pages/Wells/containers/ChartYScaleProvider';
import { Title, Text } from 'components/Typography';
import Box, { Flexbox } from 'components/Box';
import { InfoCircleOutlined } from '@ant-design/icons';
import XLegendSwitch from 'pages/Wells/pages/WellPlanning/components/XLegendSwitch';
import { useTheme } from 'styled-components';
import { useChartYScale } from 'pages/Wells/containers/ChartYScaleProvider';
import EmissionReductionProvider, {
  useEmissionReduction,
} from '../EmissionReductionProvider';
import useCurrentWellPlan from 'pages/WellPlan/hooks/useCurrentWellPlan';
import EmissionReductionFilters from '../EmissionReductionFilters';
import CO2EmissionReductionChart from '../CO2EmissionReductionChart';
import { MeasuredValue } from 'pages/Wells/consts';
import useEmissionReductionInitiatives from 'pages/Wells/hooks/useEmissionReductionInitiatives';
import ValueSwitch from 'pages/Wells/pages/WellPlanning/components/ValueSwitch';

const EmissionReduction = () => {
  const [{ value, xLegend }, dispatch] = useEmissionReduction();
  const { colors } = useTheme();
  const { yScalesWidths } = useChartYScale();
  const marginLeft = yScalesWidths['y'] || 0;
  return (
    <>
      <Flexbox alignItems="center">
        <Title level={4}>Potential emission reduction</Title>
        <Box marginLeft={6}>
          <Text fontSize={16}>
            <InfoCircleOutlined />
          </Text>
        </Box>
      </Flexbox>
      <Flexbox justifyContent="space-between">
        <Box marginTop={17}>
          <ValueSwitch
            value={value}
            onChange={(event) =>
              dispatch({
                type: 'changeValue',
                value: event.target.value,
              })
            }
          />
        </Box>
        <Box marginTop={32}>
          <EmissionReductionFilters />
        </Box>
      </Flexbox>
      <Box marginTop={12}>
        {value === MeasuredValue.CO2 ? <CO2EmissionReductionChart /> : null}
      </Box>
      <Flexbox alignItems="center" marginTop={6} marginLeft={marginLeft}>
        <Flexbox flexShrink={0}>
          <XLegendSwitch
            value={xLegend}
            onChange={(checked) =>
              dispatch({
                type: 'changeXLegend',
                xLegend: checked ? 'dates' : 'days',
              })
            }
          />
        </Flexbox>
        <Flexbox justifyContent="center" flexGrow={1}>
          <Text color={colors.gray['10']}>
            Target daily emission reduction initiatives
          </Text>
        </Flexbox>
      </Flexbox>
    </>
  );
};

const DefaultEmissionReduction = () => {
  const { wellPlanId } = useCurrentWellPlan();
  const { isLoading: isLoadingEmissionReductionInitiatives } =
    useEmissionReductionInitiatives(wellPlanId);
  if (isLoadingEmissionReductionInitiatives) {
    return null;
  }

  return (
    <ChartYScaleProvider>
      <EmissionReductionProvider wellPlanId={wellPlanId}>
        <EmissionReduction />
      </EmissionReductionProvider>
    </ChartYScaleProvider>
  );
};

export default DefaultEmissionReduction;
