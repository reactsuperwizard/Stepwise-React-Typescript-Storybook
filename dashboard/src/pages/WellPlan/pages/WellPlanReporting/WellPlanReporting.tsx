import { FilePdfOutlined } from '@ant-design/icons';
import { Spin } from 'antd';
import Box, { Flexbox } from 'components/Box';
import Button from 'components/Button';
import Center from 'components/Center';
import Result from 'components/Result';
import { Title } from 'components/Typography';
import WellPlanSteps from 'pages/WellPlan/components/WellPlanSteps';
import ReportProvider from 'pages/WellPlan/containers/ReportProvider';
import useExportPDF from './useExportPDF';
import useWellPlanReporting from './useWellPlanReporting';
import useCurrentWellPlan from 'pages/WellPlan/hooks/useCurrentWellPlan';
import ChartYScaleProvider from 'pages/Wells/containers/ChartYScaleProvider';
import WellReportCO2 from './WellReportCO2';
import WellReportCO2ChartFiltersProvider from './WellReportCO2ChartFiltersProvider';
import WellReportSummary from './WellReportSummary';
import { WellPlanStep } from 'pages/WellPlan/consts';
import WellName from 'pages/Wells/containers/WellName';

const WellPlanReporting = () => {
  const { data: wellPlanData, wellPlanId } = useCurrentWellPlan();
  const { isLoading, error } = useWellPlanReporting();
  const { onExportPDF, isExportingPDF } = useExportPDF(wellPlanId);

  if (isLoading) {
    return (
      <Center mt={248}>
        <Spin size="large" />
      </Center>
    );
  }
  if (error) {
    return (
      <Center mt={248}>
        <Result
          status="error"
          subTitle="Unable to load well completed report right now"
        />
      </Center>
    );
  }
  return (
    <Box marginTop={44} marginBottom={28} marginX={28} overflowX="hidden">
      <WellPlanSteps
        wellPlanCurrentStep={wellPlanData?.current_step}
        wellPlanId={wellPlanData?.id}
        activeStep={WellPlanStep.Analysis}
      />

      <Box marginTop={32}>
        <WellName />
      </Box>

      <Box marginTop={22} marginBottom={15}>
        <Title level={5}>Well analysis and reporting</Title>
      </Box>

      <ReportProvider>
        <Box>
          <WellReportSummary />

          <Flexbox marginTop={7} justifyContent="flex-end">
            <Button
              type="primary"
              icon={<FilePdfOutlined />}
              onClick={onExportPDF}
              disabled={isExportingPDF}
            >
              Export PDF
            </Button>
          </Flexbox>

          <Box
            height={1}
            backgroundColor="gray.6"
            marginTop={27}
            marginBottom={31}
          />

          <ChartYScaleProvider>
            <WellReportCO2ChartFiltersProvider>
              <WellReportCO2 />
            </WellReportCO2ChartFiltersProvider>
          </ChartYScaleProvider>
        </Box>
      </ReportProvider>
    </Box>
  );
};

export default WellPlanReporting;
