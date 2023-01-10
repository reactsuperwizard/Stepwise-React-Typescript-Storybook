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
    await TenantsService.tenantsEmissionsWellsPlannedEmissionsTargetCo2List(
      tenantId,
      wellPlanId,
    );
  return data;
}

const useTargetCO2Emissions = (wellPlanId: number) => {
  const { tenantId } = useTenant();

  return useQuery(
    tenantId
      ? wellsQueryKeys.wellPlanTargetCO2Emissions({
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

export default useTargetCO2Emissions;
