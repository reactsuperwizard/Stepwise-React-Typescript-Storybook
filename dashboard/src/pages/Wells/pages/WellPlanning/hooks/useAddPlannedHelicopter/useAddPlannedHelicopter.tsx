import { TenantsService, WellPlannerDetails } from 'api/schema';
import { FormikHelpers } from 'formik';
import useTenant from 'hooks/useTenant';

import { notification } from 'antd';
import {
  FormValues,
  getInitialValues,
  normalizeFormValues,
  schema,
} from 'pages/Wells/containers/HelicopterForm';
import useInvalidatePlannedEmissionsCache from 'pages/Wells/hooks/useInvalidatePlannedEmissionsCache';
import useWellPlanCache from 'pages/WellPlan/hooks/useWellPlanCache';
import { useMutation } from 'react-query';
import { apiValidationErrors } from 'utils/api';
import Logger from 'utils/logger';

const useAddPlannedHelicopter = ({
  wellPlanId,
  onSuccess,
}: {
  wellPlanId: number;
  onSuccess: () => void;
}) => {
  const { tenantId } = useTenant();
  const { setWellPlanData } = useWellPlanCache(wellPlanId);
  const invalidatePlannedEmissionsCache = useInvalidatePlannedEmissionsCache();
  const addPlannedHelicopterMutation = useMutation<
    WellPlannerDetails,
    Error,
    {
      values: FormValues;
      formikHelpers: FormikHelpers<FormValues>;
    }
  >(
    async ({ values }) => {
      const { data } =
        await TenantsService.tenantsEmissionsWellsPlannedHelicopterUsesCreateCreate(
          Number(tenantId),
          Number(wellPlanId),
          normalizeFormValues(values),
        );

      return data;
    },
    {
      onSuccess: async (data, { values }) => {
        setWellPlanData(data);
        const helicopterType = data.planned_helicopter_uses.find(
          (helicopterUse) =>
            helicopterUse.helicopter_type.id === values.helicopter_type,
        )?.helicopter_type.type;
        notification.success({
          message: 'Added helicopter',
          description: (
            <>
              Helicopter <strong>{helicopterType}</strong> has been added.
            </>
          ),
        });
        await invalidatePlannedEmissionsCache(data.id);
        onSuccess();
      },
      onError: (error, { formikHelpers, values }) => {
        const { nonFieldErrors, fieldErrors } = apiValidationErrors(
          error,
          'Unable to add a new helicopter. Please try later.',
        );

        Logger.error(
          `Unable to add a new planned helicopter use to WellPlanner(id=${wellPlanId}).`,
          error,
          values,
        );
        formikHelpers.setStatus(nonFieldErrors);
        formikHelpers.setErrors(fieldErrors);
      },
    },
  );
  return {
    initialValues: getInitialValues(),
    validationSchema: schema,
    addPlannedHelicopterMutation,
  };
};

export default useAddPlannedHelicopter;
