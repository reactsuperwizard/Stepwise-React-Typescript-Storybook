import { MaterialTypeList } from 'api/schema';
import { useAddEditActions } from 'containers/AddEditActionsProvider';
import { usePaginationProvider } from 'components/PaginationProvider';
import { AddFormDrawer } from 'containers/FormDrawer';
import useAddMaterialType from '../../hooks/useAddMaterialType';
import { AssetListAddEditActionContext } from '../../types';
import MaterialTypeForm, { FormValues } from '../MaterialTypeForm';

const AddMaterialTypeDrawer = () => {
  const { onCloseDrawer } =
    useAddEditActions<AssetListAddEditActionContext>('materials');
  const pagination = usePaginationProvider();
  const onSuccess = () => {
    onCloseDrawer();
    pagination.reset();
  };
  const {
    validationSchema,
    addMaterialTypeMutation: {
      mutateAsync: onAddMaterialType,
      isLoading: isAddingMaterialType,
    },
    initialValues,
  } = useAddMaterialType({
    onSuccess,
  });

  return (
    <AddFormDrawer<FormValues, MaterialTypeList, AssetListAddEditActionContext>
      title="Add material type"
      initialValues={initialValues}
      validationSchema={validationSchema}
      onSubmit={onAddMaterialType}
      isSubmitting={isAddingMaterialType}
      width={600}
      context="materials"
    >
      <MaterialTypeForm />
    </AddFormDrawer>
  );
};

export default AddMaterialTypeDrawer;
