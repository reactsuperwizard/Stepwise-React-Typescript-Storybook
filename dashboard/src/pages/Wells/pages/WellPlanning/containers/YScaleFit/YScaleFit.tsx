import { Scale } from 'chart.js';
import { useCallback } from 'react';
import 'chartjs-adapter-date-fns';
import { useChartYScale } from 'pages/Wells/containers/ChartYScaleProvider';

interface YScaleFitProps {
  children: (afterYScaleFit: (scale: Scale) => void) => JSX.Element;
}

const YScaleFit = ({ children }: YScaleFitProps) => {
  const { setYScale } = useChartYScale();
  const afterYScaleFit = useCallback(
    (scale: Scale) => {
      setYScale(scale);
    },
    [setYScale],
  );

  return children(afterYScaleFit);
};

export default YScaleFit;
