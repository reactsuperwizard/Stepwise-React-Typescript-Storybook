import Center from 'components/Center';
import { Spin } from 'antd';
import Box from 'components/Box';
import useCO2EmissionsTargetChart from '../../hooks/useCO2EmissionsTargetChart';
import YScaleFit from 'pages/Wells/pages/WellPlanning/containers/YScaleFit';
import CO2EmissionsTargetTooltip from 'pages/Wells/pages/WellPlanning/containers/CO2EmissionsTargetTooltip';
import EmissionBarChart from 'pages/Wells/pages/WellPlanning/containers/EmissionBarChart';
import useExternalTooltipHandler from 'pages/Wells/hooks/useExternalTooltipHandler/useExternalTooltipHandler';
import { useEmissionsTarget } from 'pages/Wells/pages/WellPlanning/containers/EmissionsTargetProvider';
import useCurrentWellPlan from 'pages/WellPlan/hooks/useCurrentWellPlan';
import { CO2EmissionsTargetTooltipProps } from 'pages/Wells/pages/WellPlanning/containers/CO2EmissionsTargetTooltip';
import { CO2 } from 'consts/format';

const CO2EmissionsTargetChart = () => {
  const { datasets, isFetching, labels } = useCO2EmissionsTargetChart();
  const { wellPlanId } = useCurrentWellPlan();
  const [{ scopes }] = useEmissionsTarget();
  const externalTooltip = useExternalTooltipHandler<
    Omit<CO2EmissionsTargetTooltipProps, 'xOverflow' | 'dataIndex'>
  >(CO2EmissionsTargetTooltip, {
    scopes,
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

export default CO2EmissionsTargetChart;
