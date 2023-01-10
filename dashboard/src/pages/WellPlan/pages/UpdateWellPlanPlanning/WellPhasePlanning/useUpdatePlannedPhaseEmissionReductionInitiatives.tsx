import { notification } from 'antd';
import { TenantsService, WellPlannerDetails } from 'api/schema';
import useTenant from 'hooks/useTenant';
import useCurrentWellPlan from 'pages/WellPlan/hooks/useCurrentWellPlan';
import useInvalidatePlannedEmissionsCache from 'pages/Wells/hooks/useInvalidatePlannedEmissionsCache';
import { useMutation } from 'react-query';
import Logger from 'utils/logger';
import useWellPlanCache from 'pages/WellPlan/hooks/useWellPlanCache';

const useUpdatePlannedPhaseEmissionReductionInitiatives = () => {
  const { tenantId } = useTenant();
  const { wellPlanId } = useCurrentWellPlan();
  const invalidatePlannedEmissionsCache = useInvalidatePlannedEmissionsCache();
  const { setWellPlanData } = useWellPlanCache(wellPlanId);

  return useMutation<
    WellPlannerDetails,
    Error,
    {
      wellPlanPhaseId: number;
      emissionReductionInitiativesIds: number[];
    }
  >(
    async ({ wellPlanPhaseId, emissionReductionInitiativesIds }) => {
      const { data } =
        await TenantsService.tenantsWellsPlannersPlannedStepsEmpInitiativesUpdateUpdate(
          Number(tenantId),
          Number(wellPlanId),
          wellPlanPhaseId,
          {
            emission_reduction_initiatives: emissionReductionInitiativesIds,
          },
        );
      return data;
    },
    {
      onSuccess: async (data) => {
        setWellPlanData(data);
        notification.success({
          message: 'Updated phase',
          description: 'EMP initiatives have been updated.',
        });
        await invalidatePlannedEmissionsCache(data.id);
      },
      onError: (error, { wellPlanPhaseId }) => {
        notification.error({
          message:
            'Unable to update EMP initiatives right now. Please try later.',
        });
        Logger.error(
          `Unable to update EMP initiatives for WellPlannerPlannedStep(id=${wellPlanPhaseId}).`,
          error,
        );
      },
    },
  );
};

export default useUpdatePlannedPhaseEmissionReductionInitiatives;
