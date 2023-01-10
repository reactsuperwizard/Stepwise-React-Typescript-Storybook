import { Flexbox } from 'components/Box';
import { Switch } from 'antd';
import { Text } from 'components/Typography';
import { useTheme } from 'styled-components';
import { SwitchChangeEventHandler } from 'antd/lib/switch';

interface XLegendSwitchProps {
  value: 'days' | 'dates';
  onChange: SwitchChangeEventHandler;
}

const XLegendSwitch = ({ value, onChange }: XLegendSwitchProps) => {
  const { colors } = useTheme();
  return (
    <Flexbox gap={4} alignItems="center">
      <Text
        color={value === 'days' ? colors.gray['10'] : colors.blue[6]}
        fontSize={8}
      >
        Days
      </Text>

      <Switch size="small" checked={value === 'dates'} onChange={onChange} />

      <Text
        color={value === 'dates' ? colors.gray['10'] : colors.blue[6]}
        fontSize={8}
      >
        Dates
      </Text>
    </Flexbox>
  );
};

export default XLegendSwitch;
