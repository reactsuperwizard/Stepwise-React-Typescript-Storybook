import FormSelect from 'components/FormSelect';
import { FormSelectProps } from 'components/FormSelect/FormSelect';
import { useField } from 'formik';
import { useEffect, useMemo } from 'react';
import useWellPlannerPhases from 'pages/WellPlan/hooks/useWellPlannerPhases';
import useWellPlannerModes from 'pages/WellPlan/hooks/useWellPlannerModes';
import useCurrentWellPlan from 'pages/WellPlan/hooks/useCurrentWellPlan';

type ModeFormSelectProps<T> = Omit<FormSelectProps<T>, 'options' | 'name'> & {
  modeName: string;
  phaseName: string;
};

const ModeFormSelect = <FormFields extends Record<string, unknown>>({
  selectInputProps,
  modeName,
  phaseName,
  ...props
}: ModeFormSelectProps<FormFields>) => {
  const { wellPlanId } = useCurrentWellPlan();
  const { data: phasesData } = useWellPlannerPhases(wellPlanId);
  const { data: modesData } = useWellPlannerModes(wellPlanId);
  const [{ value: phaseValue }] = useField(phaseName);
  const [{ value: modeValue }, , { setValue: setModeValue }] =
    useField(modeName);

  const selectedPhase = useMemo(
    () => phasesData?.find((phaseData) => phaseData.id === phaseValue),
    [phasesData, phaseValue],
  );

  const selectedMode = useMemo(
    () => modesData?.find((modeData) => modeData.id === modeValue),
    [modesData, modeValue],
  );

  const modeOptions = useMemo(() => {
    const modes = selectedPhase?.transit
      ? modesData?.filter((modeData) => modeData.transit)
      : modesData?.filter((modeData) => !modeData.transit);
    return (
      modes?.map((modeData) => ({
        label: modeData.name,
        value: modeData.id,
      })) ?? []
    );
  }, [selectedPhase, modesData]);
  useEffect(() => {
    if (selectedPhase?.transit && !selectedMode?.transit) {
      setModeValue(modesData?.find((modeData) => modeData.transit)?.id || null);
    }
    if (selectedPhase && !selectedPhase?.transit && selectedMode?.transit) {
      setModeValue(null);
    }
  }, [selectedPhase, selectedMode, modesData, phaseValue, setModeValue]);

  return (
    <FormSelect<FormFields>
      name={modeName}
      options={modeOptions}
      selectInputProps={{
        disabled: selectedPhase?.transit ?? true,
        ...selectInputProps,
      }}
      {...props}
    />
  );
};

const DefaultModeFormSelect = <FormFields extends Record<string, unknown>>(
  props: ModeFormSelectProps<FormFields>,
) => {
  const { wellPlanId } = useCurrentWellPlan();
  const { isLoading: isLoadingPhases } = useWellPlannerPhases(wellPlanId);
  const { isLoading: isLoadingModes } = useWellPlannerModes(wellPlanId);

  if (isLoadingPhases || isLoadingModes) {
    return null;
  }

  return <ModeFormSelect {...props} />;
};

export default DefaultModeFormSelect;
