import useDimensions from 'hooks/useDimensions';
import { useMemo } from 'react';

const useMeasureInputsHeight = () => {
  const [ref, size] = useDimensions<HTMLDivElement>();
  const inputsHeight = useMemo(() => {
    if (size) {
      return window.innerHeight - size.top - 142;
    }
    return 0;
  }, [size]);

  return {
    inputsHeight,
    inputsHeightRef: ref,
  };
};

export default useMeasureInputsHeight;
