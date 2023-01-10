import useCurrentWellPlan from 'pages/WellPlan/hooks/useCurrentWellPlan';
import { Text } from 'components/Typography';
import { InfoCircleOutlined } from '@ant-design/icons';
import { useTheme } from 'styled-components';
import { useState } from 'react';
import WellDetailsModal from 'pages/Wells/containers/WellDetailsModal';

const WellName = () => {
  const { data: wellPlanData } = useCurrentWellPlan();
  const { colors } = useTheme();
  const [showDetails, setShowDetails] = useState(false);

  return (
    <>
      <Text fontSize={16} lineHeight="24px">
        Well:{' '}
        <a onClick={() => setShowDetails(true)}>
          <Text color={colors.purple[11]} underline strong marginRight={4}>
            {wellPlanData?.name.name}
          </Text>
          <InfoCircleOutlined style={{ color: colors.purple[11] }} />
        </a>
        <Text marginLeft={8}>
          Sidetrack: <Text strong>{wellPlanData?.sidetrack}</Text>
        </Text>
      </Text>
      <WellDetailsModal
        wellData={wellPlanData}
        visible={showDetails}
        onCancel={() => setShowDetails(false)}
      />
    </>
  );
};

export default WellName;
