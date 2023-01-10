import AddEditModal from 'containers/AddEditModal';
import MaterialTypeForm from 'pages/Assets/pages/AssetList/containers/MaterialTypeForm';
import { useAddEditSelect } from 'components/AddEditSelect';
import useAddMaterialType from 'pages/Assets/pages/AssetList/hooks/useAddMaterialType';

const AddMaterialTypeModal = () => {
  const { onClose, isAdding } = useAddEditSelect();
  const {
    validationSchema,
    addMaterialTypeMutation: { mutateAsync: onAddMaterialType },
    initialValues,
  } = useAddMaterialType({
    onSuccess: onClose,
  });
  return (
    <AddEditModal
      schema={validationSchema}
      initialValues={initialValues}
      title="Add material type"
      okText="Add"
      visible={isAdding}
      onCancel={onClose}
      onSubmit={(values, formikHelpers) =>
        onAddMaterialType({
          values,
          formikHelpers,
        })
      }
    >
      <MaterialTypeForm />
    </AddEditModal>
  );
};

export default AddMaterialTypeModal;
