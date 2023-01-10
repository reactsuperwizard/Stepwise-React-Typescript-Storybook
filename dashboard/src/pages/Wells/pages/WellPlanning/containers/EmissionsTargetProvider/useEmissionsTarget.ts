import { useContext } from 'react';
import { EmissionsTargetProviderContext } from './EmissionsTargetProvider';

const useEmissionsTarget = () => {
  const context = useContext(EmissionsTargetProviderContext);
  if (!context) {
    throw new Error(
      'useEmissionsTarget can not be used outside of EmissionsTargetProvider',
    );
  }
  return context;
};

export default useEmissionsTarget;
