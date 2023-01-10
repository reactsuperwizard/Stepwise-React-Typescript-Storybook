import Box, { Flexbox } from 'components/Box';
import { Text } from 'components/Typography';
import { useTheme } from 'styled-components';

interface TooltipHeaderProps {
  title: string;
  color?: string;
}

const TooltipHeader = ({ title, color }: TooltipHeaderProps) => {
  const { colors } = useTheme();
  return (
    <Flexbox gap={6} alignItems="center" paddingY={5}>
      {color ? (
        <Box
          size={10}
          height={10}
          borderRadius="50%"
          backgroundColor={color}
          flexShrink={0}
        />
      ) : null}
      <Text
        fontSize={8}
        lineHeight="14px"
        color={colors.gray[10]}
        fontWeight={600}
      >
        {title}
      </Text>
    </Flexbox>
  );
};

export default TooltipHeader;
