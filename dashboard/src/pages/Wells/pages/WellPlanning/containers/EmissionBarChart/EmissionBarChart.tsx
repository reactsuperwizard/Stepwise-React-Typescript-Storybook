import {
  Chart,
  ChartDataset,
  ChartTypeRegistry,
  Scale,
  ScaleOptionsByType,
  TooltipOptions,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';
import { useTheme } from 'styled-components';
import { memo } from 'react';
import zoomPlugin from 'chartjs-plugin-zoom';
import 'chartjs-adapter-date-fns';

Chart.register(zoomPlugin);

export interface EmissionBarChartProps {
  datasets: (ChartDataset<'bar'> | ChartDataset<'line'>)[];
  labels: string[];
  afterYScaleFit?: (scale: Scale) => void;
  yScales?: Record<
    string,
    ScaleOptionsByType<ChartTypeRegistry['line']['scales']>
  >;
  onComplete?: (this: Chart, event: unknown) => void;
  externalTooltip?: TooltipOptions<'bar'>['external'];
  yScaleTitle: string;
}

function EmissionBarChart({
  datasets,
  afterYScaleFit,
  yScales,
  onComplete,
  labels,
  externalTooltip,
  yScaleTitle,
}: EmissionBarChartProps) {
  const { colors } = useTheme();
  if (yScales && afterYScaleFit) {
    for (const key of Object.keys(yScales)) {
      yScales[key].afterFit = afterYScaleFit;
    }
  }
  return (
    <Bar
      data={{
        labels,
        datasets: datasets as ChartDataset<'bar'>[],
      }}
      options={{
        animation: {
          onComplete,
        },
        maintainAspectRatio: false,
        datasets: {
          bar: {
            maxBarThickness: 26,
          },
          line: {
            tension: 0.2,
            borderDash: [4, 2],
            pointRadius: 0,
            borderWidth: 1,
          },
        },
        plugins: {
          zoom: {
            pan: {
              enabled: true,
              mode: 'x',
            },
          },
          legend: {
            display: false,
          },
          tooltip: {
            enabled: false,
            external: externalTooltip,
            position: 'nearest',
          },
        },
        scales: {
          x: {
            stacked: true,
            ticks: {
              font: {
                size: 12,
                lineHeight: '20px',
                family: 'Manrope',
              },
              color: colors.blue[6],
            },
            grid: {
              color: colors.gray[4],
            },
            min: 0,
            max: 29, // 30 days
          },
          y: {
            title: {
              text: yScaleTitle,
              font: {
                size: 10,
                lineHeight: 1.6,
                family: 'Manrope',
              },
              color: colors.gray[6],
              display: true,
            },
            stacked: true,
            beginAtZero: true,
            grid: {
              display: false,
            },
            afterFit: afterYScaleFit,
            ticks: {
              font: {
                size: 10,
                lineHeight: 1.6,
                family: 'Manrope',
              },
              color: colors.gray[6],
            },
          },
          ...yScales,
        },
      }}
    />
  );
}

export default memo(EmissionBarChart);
