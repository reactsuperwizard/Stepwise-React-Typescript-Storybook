import { useEffect, useMemo } from 'react';
import { useField } from 'formik';
import {
  AddEditSelectProvider,
  useAddEditSelect,
} from 'components/AddEditSelect';
import FormAddEditSelect from 'components/FormAddEditSelect';
import { FormSelectProps } from 'components/FormSelect/FormSelect';
import useAllMaterialTypes from 'pages/WellPlan/hooks/useAllMaterialTypes';
import AddMaterialTypeModal from '../AddMaterialTypeModal';
import EditMaterialTypeModal from '../EditMaterialTypeModal';

type MaterialTypeFormSelectProps<T> = Omit<
  FormSelectProps<T>,
  'options' | 'name'
> & {
  materialTypeName: string;
  materialCategoryName: string;
};

const MaterialTypeFormSelect = <FormFields extends Record<string, unknown>>({
  selectInputProps,
  materialTypeName,
  materialCategoryName,
  ...props
}: MaterialTypeFormSelectProps<FormFields>) => {
  const { data: allMaterialTypes } = useAllMaterialTypes();
  const { onAdd, onEdit } = useAddEditSelect();
  const [{ value: materialTypeValue }, , { setValue: setMaterialTypeValue }] =
    useField(materialTypeName);
  const [{ value: materialCategoryValue }] = useField(materialCategoryName);

  const materialCategoryTypes = useMemo(
    () =>
      allMaterialTypes?.filter(
        (materialType) => materialType.category === materialCategoryValue,
      ),
    [allMaterialTypes, materialCategoryValue],
  );
  const options = useMemo(
    () =>
      materialCategoryTypes?.map((materialCategoryType) => ({
        label: materialCategoryType.type,
        value: materialCategoryType.id,
        editable: true,
      })) ?? [],
    [materialCategoryTypes],
  );

  useEffect(() => {
    if (
      materialTypeValue &&
      materialCategoryTypes &&
      !materialCategoryTypes.find(
        (materialCategoryType) => materialCategoryType.id === materialTypeValue,
      )
    ) {
      setMaterialTypeValue(null);
    }
  }, [
    materialTypeValue,
    materialCategoryValue,
    materialCategoryTypes,
    setMaterialTypeValue,
  ]);

  return (
    <>
      <FormAddEditSelect<FormFields>
        name={materialTypeName}
        options={options}
        addEditSelectInputProps={{
          ...selectInputProps,
          disabled: !materialCategoryValue,
          addNewLabel: 'Add type',
          onAdd,
          onEdit,
        }}
        {...props}
      />
      <AddMaterialTypeModal />
      <EditMaterialTypeModal />
    </>
  );
};

const DefaultMaterialTypeFormSelect = <
  FormFields extends Record<string, unknown>,
>(
  props: MaterialTypeFormSelectProps<FormFields>,
) => {
  return (
    <AddEditSelectProvider>
      <MaterialTypeFormSelect {...props} />
    </AddEditSelectProvider>
  );
};

export default DefaultMaterialTypeFormSelect;
