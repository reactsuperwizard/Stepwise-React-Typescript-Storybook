import { Radio } from 'antd';
import { MeasuredValue } from 'pages/Wells/consts';
import { RadioChangeEvent } from 'antd/lib/radio/interface';

interface ValueSwitchProps {
  value: MeasuredValue;
  onChange: (e: RadioChangeEvent) => void;
  disabled?: {
    co2?: boolean;
    nox?: boolean;
    fuel?: boolean;
    fuelCost?: boolean;
  };
}

const ValueSwitch = ({ value, onChange, disabled }: ValueSwitchProps) => {
  return (
    <Radio.Group buttonStyle="solid" onChange={onChange} defaultValue={value}>
      <Radio.Button value={MeasuredValue.CO2} disabled={disabled?.co2}>
        CO
        <sub>2</sub>
      </Radio.Button>
      <Radio.Button value={MeasuredValue.NOx} disabled={disabled?.nox}>
        NOx
      </Radio.Button>
      <Radio.Button value={MeasuredValue.Fuel} disabled={disabled?.fuel}>
        Fuel
      </Radio.Button>
      <Radio.Button
        value={MeasuredValue.FuelCost}
        disabled={disabled?.fuelCost}
      >
        Fuel cost
      </Radio.Button>
    </Radio.Group>
  );
};

export default ValueSwitch;
