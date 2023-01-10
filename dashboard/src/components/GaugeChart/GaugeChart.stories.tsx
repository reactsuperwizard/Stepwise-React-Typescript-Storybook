import { ComponentStory, ComponentMeta } from '@storybook/react';
import Box from 'components/Box';
import GaugeChart from './GaugeChart';

export default {
  title: 'components/GaugeChart',
  component: GaugeChart,
  argTypes: {},
} as ComponentMeta<typeof GaugeChart>;

const Template: ComponentStory<typeof GaugeChart> = (args) => (
  <Box width={400}>
    <GaugeChart {...args} />
  </Box>
);
export const Default = Template.bind({});

Default.args = {
  labels: [
    {
      name: 'Baseline',
      value: 1120,
      color: '#40536A',
    },
    {
      name: 'Target',
      value: 810,
      color: '#E3E3F4',
    },
    {
      name: 'Measured',
      value: 950,
      color: '#7471C6',
    },
  ],
  plotValues: [950, 550],
  needleValues: [810, 1120],
  plotColors: ['#7471C6', '#E3E3F4'],
  needleColors: ['#D0D5DD', '#40536A'],
};
