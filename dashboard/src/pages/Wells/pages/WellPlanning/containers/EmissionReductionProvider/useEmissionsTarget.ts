import { useContext } from 'react';
import { EmissionReductionProviderContext } from './EmissionReductionProvider';

const useEmissionReduction = () => {
  const context = useContext(EmissionReductionProviderContext);
  if (!context) {
    throw new Error(
      'useEmissionReduction can not be used outside of EmissionReductionProvider',
    );
  }
  return context;
};

export default useEmissionReduction;
