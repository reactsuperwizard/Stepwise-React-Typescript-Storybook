import { Flexbox } from 'components/Box';
import { Text } from 'components/Typography';
import { prettyNumber, roundNumber } from 'utils/format';

interface TooltipTotalProps {
  value: number;
  unit: React.ReactNode;
}

const TooltipTotal = ({ value, unit }: TooltipTotalProps) => {
  return (
    <Flexbox paddingY={5} justifyContent="flex-end">
      <Text fontSize={10} lineHeight="16px" fontWeight={600}>
        {prettyNumber(roundNumber(value, 2))} {unit}
      </Text>
    </Flexbox>
  );
};

export default TooltipTotal;
