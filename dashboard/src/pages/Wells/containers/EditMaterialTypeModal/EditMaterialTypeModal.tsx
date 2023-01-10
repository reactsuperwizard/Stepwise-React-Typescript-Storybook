import MaterialTypeForm from 'pages/Assets/pages/AssetList/containers/MaterialTypeForm';
import AddEditModal from 'containers/AddEditModal';
import { useAddEditSelect } from 'components/AddEditSelect';
import useEditMaterialType from 'pages/Assets/pages/AssetList/hooks/useEditMaterialType';
import useAllMaterialTypes from 'pages/WellPlan/hooks/useAllMaterialTypes';
import { useMemo } from 'react';

const EditMaterialTypeModal = () => {
  const { onClose, editedOption } = useAddEditSelect();
  const { data: allMaterialTypes } = useAllMaterialTypes();

  const materialTypeToEdit = useMemo(
    () =>
      editedOption
        ? allMaterialTypes?.find(
            (materialType) => materialType.id === editedOption,
          )
        : undefined,
    [editedOption, allMaterialTypes],
  );
  const {
    validationSchema,
    editMaterialTypeMutation: { mutateAsync: onEditMaterialType },
    initialValues,
  } = useEditMaterialType({
    onSuccess: onClose,
    materialType: materialTypeToEdit,
  });

  return (
    <AddEditModal
      schema={validationSchema}
      initialValues={initialValues}
      title="Edit material type"
      okText="Update"
      visible={!!materialTypeToEdit}
      onCancel={onClose}
      onSubmit={(values, formikHelpers) =>
        onEditMaterialType({
          values,
          formikHelpers,
        })
      }
    >
      <MaterialTypeForm edit />
    </AddEditModal>
  );
};

export default EditMaterialTypeModal;
