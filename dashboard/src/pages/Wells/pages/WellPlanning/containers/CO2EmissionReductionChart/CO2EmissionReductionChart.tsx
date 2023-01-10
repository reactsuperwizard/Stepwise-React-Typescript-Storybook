import useCurrentWellPlan from 'pages/WellPlan/hooks/useCurrentWellPlan';
import useExternalTooltipHandler from 'pages/Wells/hooks/useExternalTooltipHandler';
import Center from 'components/Center';
import { Spin } from 'antd';
import Box from 'components/Box';
import YScaleFit from 'pages/Wells/pages/WellPlanning/containers/YScaleFit';
import EmissionBarChart from 'pages/Wells/pages/WellPlanning/containers/EmissionBarChart/EmissionBarChart';
import { CO2 } from 'consts/format';
import useCO2EmissionReductionChart from '../../hooks/useCO2EmissionReductionChart';
import { useEmissionReduction } from '../EmissionReductionProvider';
import CO2EmissionReductionTooltip, {
  CO2EmissionReductionTooltipProps,
} from '../CO2EmissionReductionTooltip';

const CO2EmissionReductionChart = () => {
  const { datasets, isFetching, labels } = useCO2EmissionReductionChart();
  const { wellPlanId } = useCurrentWellPlan();
  const [{ emissionReductionInitiatives: emissionReductionInitiativeFilters }] =
    useEmissionReduction();
  const externalTooltip = useExternalTooltipHandler<
    Omit<CO2EmissionReductionTooltipProps, 'xOverflow' | 'dataIndex'>
  >(CO2EmissionReductionTooltip, {
    emissionReductionInitiativeFilters,
    wellPlanId,
  });

  if (isFetching) {
    return (
      <Center height={256}>
        <Spin />
      </Center>
    );
  }

  return (
    <Box height={256}>
      <YScaleFit>
        {(afterYScaleFit) => (
          <EmissionBarChart
            afterYScaleFit={afterYScaleFit}
            datasets={datasets}
            labels={labels}
            externalTooltip={externalTooltip}
            yScaleTitle={`${CO2} Te`}
          />
        )}
      </YScaleFit>
    </Box>
  );
};

export default CO2EmissionReductionChart;
