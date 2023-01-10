import useShowColumns from 'hooks/useShowColumns';

export type PhaseListShowableColumns = {
  phase: boolean;
  mode: boolean;
  duration: boolean;
  waitingOnWeather: boolean;
  season: boolean;
  carbonCaptureStorageSystemQuantity: boolean;
  sectionLength: boolean;
  emissionReductionInitiatives: boolean;
  comment: boolean;
  externalEnergySupplyEnabled: boolean;
  externalEnergySupplyQuota: boolean;
  materials: boolean;
};

const initialValues: PhaseListShowableColumns = {
  phase: true,
  mode: true,
  duration: true,
  waitingOnWeather: true,
  season: true,
  carbonCaptureStorageSystemQuantity: true,
  sectionLength: true,
  emissionReductionInitiatives: false,
  comment: true,
  externalEnergySupplyEnabled: true,
  externalEnergySupplyQuota: false,
  materials: true,
};

const useShowPhasesColumns = () => {
  return useShowColumns<PhaseListShowableColumns>({
    name: 'wellPhaseList',
    initialValues,
  });
};

export default useShowPhasesColumns;
