import wellsQueryKeys from 'api/queryKeys/wells';
import useTenant from 'hooks/useTenant';
import { useCallback } from 'react';
import { useQueryClient } from 'react-query';

const useInvalidatePlannedEmissionsCache = () => {
  const { tenantId } = useTenant();
  const queryClient = useQueryClient();
  return useCallback(
    async (wellPlanId: number) => {
      if (!tenantId) {
        throw new Error('Missing tenant id');
      }
      await Promise.all([
        queryClient.invalidateQueries(
          wellsQueryKeys.wellPlanPlannedEmissions({ tenantId, wellPlanId }),
        ),
      ]);
    },
    [queryClient, tenantId],
  );
};

export default useInvalidatePlannedEmissionsCache;
