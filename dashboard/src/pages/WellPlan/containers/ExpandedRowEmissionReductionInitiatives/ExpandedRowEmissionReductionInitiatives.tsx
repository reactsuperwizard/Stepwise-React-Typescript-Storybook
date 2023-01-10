import { Col } from 'antd';
import {
  EmissionReductionInitiativeList,
  EmissionReductionInitiativeTypeEnum,
  WellPlannerDetailsCompleteStep,
  WellPlannerDetailsPlannedStep,
} from 'api/schema';
import Box from 'components/Box';
import { Row } from 'components/Grid';
import { Text } from 'components/Typography';
import { EMISSION_REDUCTION_INITIATIVE_TYPE_NAME_MAP } from 'pages/WellPlan/consts';
import useCurrentWellPlan from 'pages/WellPlan/hooks/useCurrentWellPlan';
import useEmissionReductionInitiatives from 'pages/Wells/hooks/useEmissionReductionInitiatives';
import { StyledCheckbox } from './ExpandedRowEmissionReductionInitiatives.styled';

interface ExpandedRowEmissionReductionInitiativesProps {
  wellPlanStep: WellPlannerDetailsPlannedStep | WellPlannerDetailsCompleteStep;
  onUpdateEmissionReductionInitiatives: (
    wellPlanPhaseId: number,
    emissionReductionInitiativeIds: number[],
  ) => void;
  editable: boolean;
}

const ExpandedRowEmissionReductionInitiatives = ({
  wellPlanStep,
  onUpdateEmissionReductionInitiatives,
  editable,
}: ExpandedRowEmissionReductionInitiativesProps) => {
  const { wellPlanId } = useCurrentWellPlan();
  const {
    data: emissionReductionInitiativesData,
    baseloads,
    powerSystems,
    productivity,
  } = useEmissionReductionInitiatives(wellPlanId);
  const renderCheckboxes = (
    emissionReductionInitiatives: EmissionReductionInitiativeList[],
    type: EmissionReductionInitiativeTypeEnum,
  ) => (
    <Col span={8}>
      <Box marginBottom={2} paddingY={3.5} marginLeft={8}>
        <Text strong>{EMISSION_REDUCTION_INITIATIVE_TYPE_NAME_MAP[type]}</Text>
      </Box>
      {emissionReductionInitiatives.map((emissionReductionInitiative) => (
        <Box key={String(emissionReductionInitiative.id)}>
          <StyledCheckbox
            disabled={!editable}
            checked={wellPlanStep.emission_reduction_initiatives.includes(
              emissionReductionInitiative.id,
            )}
            onClick={() =>
              wellPlanStep.emission_reduction_initiatives.includes(
                emissionReductionInitiative.id,
              )
                ? onUpdateEmissionReductionInitiatives(
                    wellPlanStep.id,
                    wellPlanStep.emission_reduction_initiatives.filter(
                      (item) => item !== emissionReductionInitiative.id,
                    ),
                  )
                : onUpdateEmissionReductionInitiatives(wellPlanStep.id, [
                    ...wellPlanStep.emission_reduction_initiatives,
                    emissionReductionInitiative.id,
                  ])
            }
          >
            {emissionReductionInitiative.name}
          </StyledCheckbox>
        </Box>
      ))}
    </Col>
  );
  return (
    <>
      <Box paddingLeft={41}>
        <StyledCheckbox
          disabled={!editable}
          checked={
            wellPlanStep.emission_reduction_initiatives.length ===
            emissionReductionInitiativesData?.length
          }
          onClick={() =>
            wellPlanStep.emission_reduction_initiatives.length ===
            emissionReductionInitiativesData?.length
              ? onUpdateEmissionReductionInitiatives(wellPlanStep.id, [])
              : onUpdateEmissionReductionInitiatives(
                  wellPlanStep.id,
                  emissionReductionInitiativesData?.map((item) => item.id) ||
                    [],
                )
          }
        >
          Select all energy reduction initiatives
        </StyledCheckbox>
        <Row gutter={[13, 20]} marginTop={5} maxWidth={750}>
          {renderCheckboxes(
            powerSystems,
            EmissionReductionInitiativeTypeEnum.POWER_SYSTEMS,
          )}
          {renderCheckboxes(
            baseloads,
            EmissionReductionInitiativeTypeEnum.BASELOADS,
          )}
          {renderCheckboxes(
            productivity,
            EmissionReductionInitiativeTypeEnum.PRODUCTIVITY,
          )}
        </Row>
      </Box>
    </>
  );
};

export default ExpandedRowEmissionReductionInitiatives;
