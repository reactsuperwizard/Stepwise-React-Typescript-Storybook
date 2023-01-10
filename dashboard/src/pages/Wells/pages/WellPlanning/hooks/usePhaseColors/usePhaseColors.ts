import { useTheme } from 'styled-components';
import { useCallback, useMemo } from 'react';

const usePhaseColors = () => {
  const { colors } = useTheme();
  const palette: string[] = useMemo(
    () => [
      colors.sand[1],
      colors.netZeroBlue[1],
      colors.netZeroBlue[3],
      colors.netZeroBlue[5],
      colors.netZeroBlue[7],
      colors.netZeroBlue[9],
      colors.deepOcean[5],
      colors.deepOcean[7],
      colors.deepOcean[9],
      colors.deepOcean[10],
      colors.turquoise[1],
    ],
    [colors.deepOcean, colors.netZeroBlue, colors.sand, colors.turquoise],
  );
  const getColor = useCallback(
    (index: number, numElements: number): string => {
      // first
      if (index === 0) {
        return palette[0];
      }
      // last
      if (index + 1 === numElements) {
        return palette[palette.length - 1];
      }
      // loop over remaining colors
      const loopPalette = palette.slice(1, numElements - 1);
      return loopPalette[(index - 1) % loopPalette.length];
    },
    [palette],
  );

  return {
    palette,
    getColor,
  };
};

export default usePhaseColors;
