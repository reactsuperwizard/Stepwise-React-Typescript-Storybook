import { Text } from 'components/Typography';
import { useTheme } from 'styled-components';
import { Flexbox } from 'components/Box';
import { Dropdown } from 'antd';
import { DownOutlined } from '@ant-design/icons';
import { DropdownButton } from './EmissionReductionFilters.styled';
import CheckboxMenu from 'components/CheckboxMenu';
import useCurrentWellPlan from 'pages/WellPlan/hooks/useCurrentWellPlan';
import useEmissionReductionInitiatives from 'pages/Wells/hooks/useEmissionReductionInitiatives';
import { useEmissionReduction } from 'pages/Wells/pages/WellPlanning/containers/EmissionReductionProvider';
import { EmissionReductionInitiativeList } from 'api/schema';
import { useCallback } from 'react';
import useEmissionReductionInitiativesColors from 'pages/WellPlan/hooks/useEmissionReductionInitiativesColors';

const EmissionReductionFilters = () => {
  const { colors } = useTheme();
  const { wellPlanId } = useCurrentWellPlan();
  const [
    { emissionReductionInitiatives: emissionReductionInitiativeFilters },
    dispatch,
  ] = useEmissionReduction();
  const { powerSystems, baseloads } =
    useEmissionReductionInitiatives(wellPlanId);
  const { getEmissionReductionInitiativeColor } =
    useEmissionReductionInitiativesColors(wellPlanId);
  const renderMenu = useCallback(
    (emissionReductionInitiatives: EmissionReductionInitiativeList[]) => (
      <CheckboxMenu
        shadow
        items={emissionReductionInitiatives.map(
          (emissionReductionInitiative) => ({
            title: emissionReductionInitiative.name,
            key: emissionReductionInitiative.id,
            checked:
              emissionReductionInitiativeFilters[
                emissionReductionInitiative.id
              ],
            color: getEmissionReductionInitiativeColor(
              emissionReductionInitiative,
            ),
          }),
        )}
        onItemChange={(emissionReductionInitiative, checked) => {
          if (checked) {
            dispatch({
              type: 'selectEmissionReductionInitiatives',
              emissionReductionInitiatives: [emissionReductionInitiative],
            });
          } else {
            dispatch({
              type: 'deselectEmissionReductionInitiatives',
              emissionReductionInitiatives: [emissionReductionInitiative],
            });
          }
        }}
        onSelectAllChange={(checked) => {
          const emissionReductionInitiativeIds =
            emissionReductionInitiatives.map(
              (emissionReductionInitiative) => emissionReductionInitiative.id,
            );
          if (checked) {
            dispatch({
              type: 'selectEmissionReductionInitiatives',
              emissionReductionInitiatives: emissionReductionInitiativeIds,
            });
          } else {
            dispatch({
              type: 'deselectEmissionReductionInitiatives',
              emissionReductionInitiatives: emissionReductionInitiativeIds,
            });
          }
        }}
      />
    ),
    [
      dispatch,
      emissionReductionInitiativeFilters,
      getEmissionReductionInitiativeColor,
    ],
  );

  return (
    <>
      <Text
        fontSize={12}
        color={colors.gray[10]}
        lineHeight="20px"
        textAlign="right"
        display="block"
      >
        Emission reduction initiatives
      </Text>
      <Flexbox marginTop={8} gap={10}>
        <Dropdown overlay={renderMenu(powerSystems)} trigger={['click']} arrow>
          <DropdownButton>
            <Flexbox gap={8} alignItems="center">
              Power systems
              <DownOutlined />
            </Flexbox>
          </DropdownButton>
        </Dropdown>
        <Dropdown overlay={renderMenu(baseloads)} trigger={['click']}>
          <DropdownButton>
            <Flexbox gap={8} alignItems="center">
              Baseloads
              <DownOutlined />
            </Flexbox>
          </DropdownButton>
        </Dropdown>
      </Flexbox>
    </>
  );
};

export default EmissionReductionFilters;
