import Box, { Flexbox } from 'components/Box';
import { Phase } from './PhaseTimeline';
import { Popover } from 'antd';
import { Text } from 'components/Typography';

interface PhaseLineProps {
  phase: Phase;
  first: boolean;
  last: boolean;
  durationPercentage: number;
  gap: number;
}

const PhaseLine = ({
  phase,
  first,
  last,
  gap,
  durationPercentage,
}: PhaseLineProps) => {
  let phaseWidth;
  if (first) {
    phaseWidth = `calc(${durationPercentage}% - ${gap / 2}px)`;
  } else if (last) {
    phaseWidth = `calc(${durationPercentage}% - ${gap / 2}px)`;
  } else {
    phaseWidth = `calc(${durationPercentage}% - ${gap}px)`;
  }
  const content = (
    <Box width={168}>
      <Flexbox gap={8} justifyContent="space-between">
        <Text fontSize={10} lineHeight="16px">
          Phase:
        </Text>
        <Text fontSize={10} lineHeight="16px" textAlign="right">
          {phase.phase}
        </Text>
      </Flexbox>
      <Flexbox gap={8} justifyContent="space-between">
        <Text fontSize={10} lineHeight="16px">
          Mode:
        </Text>
        <Text fontSize={10} lineHeight="16px" textAlign="right">
          {phase.mode}
        </Text>
      </Flexbox>
    </Box>
  );

  return (
    <Popover placement="top" content={content} trigger="hover">
      <Box
        width={phaseWidth}
        backgroundColor={phase.color}
        height={8}
        borderRadius={5}
      />
    </Popover>
  );
};

export default PhaseLine;
