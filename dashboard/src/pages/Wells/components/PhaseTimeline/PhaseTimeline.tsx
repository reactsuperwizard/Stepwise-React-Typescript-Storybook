import Box, { Flexbox } from 'components/Box';
import PhaseLine from './PhaseLine';
import { Text } from 'components/Typography';

export interface Phase {
  phase: string;
  mode: string;
  color: string;
  duration: number;
}

interface PhaseTimelineProps {
  title: string;
  phases: Phase[];
  totalDuration: number;
}

const PhaseTimeline = ({
  title,
  phases,
  totalDuration,
}: PhaseTimelineProps) => {
  const gap = 3;
  return (
    <>
      <Text fontSize={12} lineHeight="20px">
        {title}
      </Text>

      <Box marginTop={9}>
        <Flexbox gap={gap} alignItems="center" width="100%">
          {phases.map((phase, index, array) => {
            return (
              <PhaseLine
                key={index}
                first={index === 0}
                last={index + 1 === array.length}
                gap={gap}
                phase={phase}
                durationPercentage={(phase.duration / totalDuration) * 100}
              />
            );
          })}
        </Flexbox>
      </Box>
    </>
  );
};

export default PhaseTimeline;
