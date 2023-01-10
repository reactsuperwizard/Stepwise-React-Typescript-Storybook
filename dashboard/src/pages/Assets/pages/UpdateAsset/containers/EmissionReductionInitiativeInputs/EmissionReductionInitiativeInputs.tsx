import { InputTable } from './EmissionReductionInitiativeInputs.styled';
import { useFormikContext } from 'formik';
import { FormValues } from 'pages/Assets/pages/UpdateAsset/containers/EmissionReductionInitiativeForm';
import useEmissionReductionInitiativeInputsColumns from 'pages/Assets/pages/UpdateAsset/hooks/useEmissionReductionInitiativeInputsColumns';
import useMeasureInputsHeight from 'pages/Assets/pages/UpdateAsset/hooks/useMeasureInputsHeight';

const EmissionReductionInitiativeInputs = () => {
  const columns = useEmissionReductionInitiativeInputsColumns();
  const { inputsHeightRef, inputsHeight } = useMeasureInputsHeight();
  const {
    values: { inputs },
  } = useFormikContext<FormValues>();
  return (
    <InputTable
      ref={inputsHeightRef}
      pagination={false}
      columns={columns}
      scroll={{
        x: 'max-content',
        y: inputsHeight ? inputsHeight : undefined,
      }}
      dataSource={inputs}
      rowKey={(record, index) => Number(index)}
    />
  );
};

export default EmissionReductionInitiativeInputs;
