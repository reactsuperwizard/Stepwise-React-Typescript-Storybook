import { Doughnut } from 'react-chartjs-2';
import { Chart, ArcElement, ChartDataset } from 'chart.js';
import ChartDataLabels from 'chartjs-plugin-datalabels';

import Box, { Flexbox } from 'components/Box';
import { Text } from 'components/Typography';
import { afterDraw } from './utils';

Chart.register(ChartDataLabels, ArcElement);

type Label = {
  name: string;
  value?: number;
  color: string;
};

interface GaugeChartProps {
  needleValues: number[];
  needleColors: string[];
  plotValues: number[];
  plotColors: string[];
  labels?: Label[];
}
export interface CustomChartDataSet<T> extends ChartDataset<'doughnut', T> {
  needleValues: number[];
  needleColors: string[];
}

const GaugeChart = ({
  needleValues,
  needleColors,
  plotColors,
  plotValues,
  labels,
}: GaugeChartProps) => {
  const datasets: CustomChartDataSet<number[]>[] = [
    {
      data: plotValues,
      backgroundColor: plotColors,
      rotation: -90,
      circumference: 180,
      needleValues,
      needleColors,
    },
  ];

  return (
    <Flexbox flexDirection={'column'}>
      <Doughnut
        data={{
          datasets,
        }}
        plugins={[
          {
            id: 'custom_draw_needle_plugin',
            afterDraw,
          },
        ]}
        options={{
          layout: {
            padding: {
              left: 0,
              top: 10,
              right: 0,
              bottom: 30,
            },
          },
          responsive: true,
          maintainAspectRatio: true,
          aspectRatio: 2,
          cutout: '80%',
          animation: false,
          elements: {
            arc: {
              borderWidth: 0,
            },
          },
          events: [],
          plugins: {
            legend: {
              display: false,
            },
            datalabels: {
              display: false,
            },
            tooltip: {
              enabled: false,
            },
          },
        }}
      />
      {labels?.length ? (
        <Flexbox gap={0} marginLeft={30}>
          {labels.map(({ name, value, color }, index) => (
            <Flexbox
              flexDirection={'column'}
              key={index}
              paddingY={4}
              paddingX={10}
            >
              <Flexbox alignItems={'center'} gap={6}>
                <Box
                  width={11}
                  height={11}
                  borderRadius="50%"
                  backgroundColor={color}
                />
                <Text color="gray.6" fontSize={12} lineHeight="20px">
                  {name}
                </Text>
              </Flexbox>
              {value ? (
                <Flexbox marginLeft={17}>
                  <Text fontSize={16} lineHeight="24px">
                    {value}
                  </Text>
                </Flexbox>
              ) : null}
            </Flexbox>
          ))}
        </Flexbox>
      ) : null}
    </Flexbox>
  );
};

export default GaugeChart;
