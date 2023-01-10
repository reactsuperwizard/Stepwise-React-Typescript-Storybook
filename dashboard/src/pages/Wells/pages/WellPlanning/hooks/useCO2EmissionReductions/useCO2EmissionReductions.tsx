import wellsQueryKeys from 'api/queryKeys/wells';
import { TenantsService } from 'api/schema';
import useTenant from 'hooks/useTenant';
import { useQuery } from 'react-query';
import { noop } from 'utils/api';

async function fetch({
  tenantId,
  wellPlanId,
}: {
  tenantId: number;
  wellPlanId: number;
}) {
  const { data } =
    await TenantsService.tenantsEmissionsWellsPlannedEmissionsTargetReductionsCo2List(
      tenantId,
      wellPlanId,
    );
  return data;
}

const useCO2EmissionReductions = (wellPlanId: number) => {
  const { tenantId } = useTenant();

  return useQuery(
    tenantId
      ? wellsQueryKeys.wellPlanTargetCO2EmissionReductions({
          tenantId,
          wellPlanId,
        })
      : [],
    tenantId
      ? () =>
          fetch({
            wellPlanId,
            tenantId,
          })
      : noop,
    {
      enabled: !!tenantId,
    },
  );
};

export default useCO2EmissionReductions;
