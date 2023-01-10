import format from 'date-fns/format';
import parseISO from 'date-fns/parseISO';
import { DATE_FORMAT_SHORT } from 'consts';
import { useMemo } from 'react';

export const useLabels = <T extends { date: string }>(
  data: T[],
  xLegend: 'days' | 'dates',
) => {
  return useMemo(() => {
    const dates = data.map((row) => row.date);
    if (xLegend === 'days') {
      return dates.map((date, index) => String(index + 1));
    } else if (xLegend === 'dates') {
      return dates.map((date) => format(parseISO(date), DATE_FORMAT_SHORT));
    }
    throw new Error(`Unknown unit type: ${xLegend}`);
  }, [data, xLegend]);
};

export default useLabels;
