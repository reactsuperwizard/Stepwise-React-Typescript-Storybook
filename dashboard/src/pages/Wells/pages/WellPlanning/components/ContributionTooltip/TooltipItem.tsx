import Box, { Flexbox } from 'components/Box';
import { Text } from 'components/Typography';
import { prettyNumber, roundNumber } from 'utils/format';

interface TooltipItemProps {
  title: string;
  value: number;
  color?: string;
  unit: React.ReactNode;
}

const TooltipItem = ({ title, value, color, unit }: TooltipItemProps) => {
  return (
    <Flexbox gap={6} alignItems="center">
      <Flexbox
        justifyContent="flex-start"
        flexGrow={1}
        gap={6}
        alignItems="center"
      >
        {color ? (
          <Box
            size={10}
            height={10}
            borderRadius="50%"
            backgroundColor={color}
            flexShrink={0}
          />
        ) : null}
        <Text fontSize={8} lineHeight="16px">
          {title}
        </Text>
      </Flexbox>
      <Flexbox justifyContent="flex-end" flexGrow={1}>
        <Text fontSize={8} lineHeight="16px">
          {prettyNumber(roundNumber(value, 2))} {unit}
        </Text>
      </Flexbox>
    </Flexbox>
  );
};

export default TooltipItem;
