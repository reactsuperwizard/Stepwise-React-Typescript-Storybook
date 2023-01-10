import { Spin } from 'antd';
import Button from 'components/Button';
import Box from 'components/Box';
import Center from 'components/Center';
import Result from 'components/Result';
import { SubmitRow } from 'components/Row';
import WellPlanSteps from 'pages/WellPlan/components/WellPlanSteps';
import AddEditActionsProvider from 'containers/AddEditActionsProvider';
import useCurrentWellPlan from 'pages/WellPlan/hooks/useCurrentWellPlan';
import useCompletePlannedPlan from 'pages/WellPlan/pages/UpdateWellPlanPlanning/useCompletePlannedPlan';
import useCanEdit from 'pages/WellPlan/hooks/useCanEdit';
import { CurrentStepEnum } from 'api/schema';
import { WellPlanStep } from 'pages/WellPlan/consts';
import PlannedVesselList from 'pages/Wells/pages/WellPlanning/containers/PlannedVesselList';
import PlannedHelicopterList from 'pages/Wells/pages/WellPlanning/containers/PlannedHelicopterList';
import PlannedPhaseList from 'pages/Wells/pages/WellPlanning/containers/PlannedPhaseList';
import PlannedStartDate from 'pages/Wells/pages/WellPlanning/containers/PlannedStartDate';
import { Title } from 'components/Typography';
import WellName from 'pages/Wells/containers/WellName';
import EmissionsTarget from 'pages/Wells/pages/WellPlanning/containers/EmissionsTarget';
import EmissionReduction from './containers/EmissionReduction';

const WellPlanning = () => {
  const {
    data: wellPlanData,
    isLoading: isLoadingWellPlan,
    error: wellPlanError,
  } = useCurrentWellPlan();
  const { mutateAsync: onCompletePlan, isLoading: isCompletingPlan } =
    useCompletePlannedPlan();
  const canEdit = useCanEdit(CurrentStepEnum.WELL_PLANNING);
  const canComplete = !(
    wellPlanData?.planned_steps.length === 0 ||
    isCompletingPlan ||
    !canEdit
  );

  if (isLoadingWellPlan) {
    return (
      <Center mt={248}>
        <Spin size="large" />
      </Center>
    );
  }

  if (wellPlanError) {
    return (
      <Center mt={248}>
        <Result status="error" subTitle="Unable to load well plan right now" />
      </Center>
    );
  }

  return (
    <Box marginTop={44} marginBottom={106} marginX={28}>
      <AddEditActionsProvider>
        <Box
          display="flex"
          flexDirection="column"
          justifyContent="space-between"
          backgroundColor="white"
        >
          <WellPlanSteps
            wellPlanCurrentStep={wellPlanData?.current_step}
            wellPlanId={wellPlanData?.id}
            activeStep={WellPlanStep.Planning}
          />

          <Box marginTop={32}>
            <WellName />
          </Box>

          <Box marginTop={22}>
            <Title level={5}>Well planning & calculations</Title>
          </Box>

          <Box marginTop={31}>
            <PlannedStartDate />
          </Box>

          <Box marginTop={8}>
            <PlannedPhaseList />
          </Box>

          <Box marginTop={19}>
            <PlannedVesselList />
          </Box>

          <Box marginTop={9}>
            <PlannedHelicopterList />
          </Box>

          {wellPlanData?.planned_steps.length ? (
            <>
              <Box marginTop={16}>
                <EmissionsTarget />
              </Box>
              <Box marginTop={24}>
                <EmissionReduction />
              </Box>
            </>
          ) : null}
        </Box>
      </AddEditActionsProvider>
      <SubmitRow>
        <Button
          type="primary"
          disabled={!canComplete}
          fontWeight={400}
          onClick={() => onCompletePlan()}
        >
          Complete well plan
        </Button>
      </SubmitRow>
    </Box>
  );
};

export default WellPlanning;
