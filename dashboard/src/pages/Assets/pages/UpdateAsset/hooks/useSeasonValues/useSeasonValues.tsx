import { useFormikContext } from 'formik';
import { FormValues } from '../../containers/BaselineForm';
import { Season } from 'pages/Assets/pages/UpdateAsset/containers/BaselineForm';

const useSeasonValues = (season: Season) => {
  const {
    values: { summer, winter },
  } = useFormikContext<FormValues>();

  const seasonValues = season === Season.Summer ? summer : winter;
  return seasonValues;
};

export default useSeasonValues;
