import Box, { Flexbox } from 'components/Box';
import { Text, Title } from 'components/Typography';
import { prettyNumber, roundNumber } from 'utils/format';
import { ArrowDownOutlined } from '@ant-design/icons';

interface TotalEmissionsProps {
  baseline: number;
  target: number;
  unit: React.ReactNode;
}

const TotalEmissions = ({ target, baseline, unit }: TotalEmissionsProps) => {
  return (
    <Flexbox gap={40}>
      <Flexbox flexDirection="column" alignItems="flex-end">
        <Text display="inline-block" type="secondary">
          Baseline
        </Text>
        <Box marginTop={4}>
          <Title level={3} fontWeight={400}>
            {prettyNumber(roundNumber(baseline, 2))} {unit}
          </Title>
        </Box>
      </Flexbox>
      <Flexbox flexDirection="column" alignItems="flex-end">
        <Text display="inline-block" type="secondary">
          Target
        </Text>
        <Flexbox marginTop={4} gap={4} alignItems="center">
          {target < baseline ? (
            <Text fontSize={24} lineHeight={1}>
              <ArrowDownOutlined />
            </Text>
          ) : null}
          <Title level={3} fontWeight={400}>
            {prettyNumber(roundNumber(target, 2))} {unit}
          </Title>
        </Flexbox>
      </Flexbox>
    </Flexbox>
  );
};

export default TotalEmissions;
