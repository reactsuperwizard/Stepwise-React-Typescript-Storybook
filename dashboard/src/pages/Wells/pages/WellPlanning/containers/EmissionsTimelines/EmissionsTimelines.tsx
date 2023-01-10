import Box from 'components/Box';
import PhaseTimeline, { Phase } from 'pages/Wells/components/PhaseTimeline';
import useCurrentWellPlan from 'pages/WellPlan/hooks/useCurrentWellPlan';
import usePhaseColors from '../../hooks/usePhaseColors';
import { sumValues } from 'utils/math';
import { useMemo } from 'react';

const EmissionsTimelines = () => {
  const { data: wellPlanData } = useCurrentWellPlan();
  const { getColor } = usePhaseColors();
  const plannedSteps = wellPlanData?.planned_steps || [];
  const totalDuration = sumValues(plannedSteps.map((step) => step.duration));
  const baselineTimeline: Phase[] = useMemo(
    () =>
      (wellPlanData?.planned_steps || []).map((plannedStep, index, array) => ({
        phase: plannedStep.phase.name,
        mode: plannedStep.mode.name,
        color: getColor(index, array.length),
        duration: plannedStep.duration,
      })),
    [getColor, wellPlanData?.planned_steps],
  );
  const targetTimeline: Phase[] = useMemo(
    () =>
      (wellPlanData?.planned_steps || []).map((plannedStep, index, array) => ({
        phase: plannedStep.phase.name,
        mode: plannedStep.mode.name,
        color: getColor(index, array.length),
        duration: plannedStep.improved_duration,
      })),
    [getColor, wellPlanData?.planned_steps],
  );

  return (
    <Box>
      <PhaseTimeline
        title="Baseline timeline"
        phases={baselineTimeline}
        totalDuration={totalDuration}
      />

      <Box marginTop={15}>
        <PhaseTimeline
          title="Target timeline"
          phases={targetTimeline}
          totalDuration={totalDuration}
        />
      </Box>
    </Box>
  );
};

export default EmissionsTimelines;
