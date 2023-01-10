import { TenantsService, WellPlannerDetails } from 'api/schema';
import useTenant from 'hooks/useTenant';
import { notification } from 'antd';
import useInvalidatePlannedEmissionsCache from 'pages/Wells/hooks/useInvalidatePlannedEmissionsCache';
import useWellPlanCache from 'pages/WellPlan/hooks/useWellPlanCache';
import { useMutation, useQueryClient } from 'react-query';
import { apiValidationErrors, isBadRequest } from 'utils/api';
import Logger from 'utils/logger';
import formatISO from 'date-fns/formatISO';
import wellsQueryKeys from 'api/queryKeys/wells';

const useUpdatePlannedStartDate = (wellPlanId: number) => {
  const { tenantId } = useTenant();
  const { setWellPlanData } = useWellPlanCache(wellPlanId);
  const queryClient = useQueryClient();
  const invalidatePlannedEmissionsCache = useInvalidatePlannedEmissionsCache();
  return useMutation<WellPlannerDetails, Error, Date>(
    async (plannedStartDate) => {
      const { data } =
        await TenantsService.tenantsEmissionsWellsPlannedStartDateUpdateUpdate(
          Number(tenantId),
          wellPlanId,
          {
            planned_start_date: formatISO(plannedStartDate, {
              representation: 'date',
            }),
          },
        );

      return data;
    },
    {
      onSuccess: async (data) => {
        setWellPlanData(data);
        notification.success({
          message: 'Updated planned start date',
        });
        await queryClient.invalidateQueries(
          wellsQueryKeys.wellEmissionReductionInitiatives(
            Number(tenantId),
            wellPlanId,
          ),
        );
        await invalidatePlannedEmissionsCache(data.id);
      },
      onError: (error, plannedStartDate) => {
        const { nonFieldErrors } = apiValidationErrors(
          error,
          'Unable to update planned start date. Please try later.',
        );
        notification.error({
          message: nonFieldErrors,
        });

        if (!isBadRequest(error)) {
          Logger.error(
            `Unable to update planned start date for WellPlanner(id=${wellPlanId}).`,
            error,
            {
              plannedStartDate,
            },
          );
        }
      },
    },
  );
};

export default useUpdatePlannedStartDate;
