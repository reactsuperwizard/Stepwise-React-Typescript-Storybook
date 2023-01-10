import wellsQueryKeys from 'api/queryKeys/wells';
import {
  EmissionReductionInitiativeTypeEnum,
  TenantsService,
} from 'api/schema';
import useTenant from 'hooks/useTenant';
import { useQuery } from 'react-query';
import { noop } from 'utils/api';
import { useMemo } from 'react';

async function fetch(tenantId: number, wellPlanId: number) {
  const { data } =
    await TenantsService.tenantsWellsPlannersEmissionReductionInitiativesList(
      tenantId,
      wellPlanId,
    );
  return data;
}

function groupByType<T extends { type: EmissionReductionInitiativeTypeEnum }>(
  data: T[],
  type: EmissionReductionInitiativeTypeEnum,
) {
  return data.filter((row) => row.type === type);
}

const useEmissionReductionInitiatives = (wellPlanId: number | undefined) => {
  const { tenantId } = useTenant();
  const enabled = !!tenantId && !!wellPlanId;

  const query = useQuery(
    enabled
      ? wellsQueryKeys.wellEmissionReductionInitiatives(tenantId, wellPlanId)
      : [],
    enabled ? () => fetch(tenantId, wellPlanId) : noop,
    {
      enabled,
    },
  );
  const { data: emissionReductionInitiativesData } = query;
  const powerSystems = useMemo(
    () =>
      groupByType(
        emissionReductionInitiativesData || [],
        EmissionReductionInitiativeTypeEnum.POWER_SYSTEMS,
      ),
    [emissionReductionInitiativesData],
  );
  const baseloads = useMemo(
    () =>
      groupByType(
        emissionReductionInitiativesData || [],
        EmissionReductionInitiativeTypeEnum.BASELOADS,
      ),
    [emissionReductionInitiativesData],
  );
  const productivity = useMemo(
    () =>
      groupByType(
        emissionReductionInitiativesData || [],
        EmissionReductionInitiativeTypeEnum.PRODUCTIVITY,
      ),
    [emissionReductionInitiativesData],
  );
  return {
    ...query,
    powerSystems,
    baseloads,
    productivity,
  };
};

export default useEmissionReductionInitiatives;
