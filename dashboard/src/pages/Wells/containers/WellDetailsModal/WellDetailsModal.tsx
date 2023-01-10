import { Col, Row } from 'antd';
import {
  DetailDateItem,
  DetailItem,
  DetailItemsProvider,
} from 'components/DetailItem';
import { WellPlannerDetails } from 'api/schema';
import { WELL_TYPE_NAME_MAP } from 'pages/Wells/consts';
import { StyledModal } from './WellDetailsModal.styled';

interface WellDetailsModalProps {
  visible: boolean;
  onCancel: () => void;
  wellData: WellPlannerDetails | undefined;
}

const WellDetailsModal = ({
  wellData,
  visible,
  onCancel,
}: WellDetailsModalProps) => {
  return (
    <StyledModal
      title="Well details"
      visible={visible}
      destroyOnClose={true}
      onCancel={onCancel}
      width={1022}
      footer={null}
    >
      <DetailItemsProvider loading={false} layout="horizontal">
        <Row gutter={[32, 8]}>
          <>
            <Col span={8}>
              <DetailItem label="Well name" value={wellData?.name.name} />
            </Col>
            <Col span={8}>
              <DetailItem label="Well location" value={wellData?.location} />
            </Col>
            <Col span={8}>
              <DetailItem label="Field" value={wellData?.field} />
            </Col>
          </>
          <>
            <Col span={8}>
              <DetailItem label="Sidetrack" value={wellData?.sidetrack} />
            </Col>
            <Col span={8}>
              <DetailItem
                label="Well type"
                value={
                  wellData?.type
                    ? WELL_TYPE_NAME_MAP[wellData.type]
                    : wellData?.type
                }
              />
            </Col>
            <Col span={8}>
              <DetailItem label="Well operator" />
            </Col>
          </>
          <>
            <Col span={8}>
              <DetailItem label="Asset manager" />
            </Col>
            <Col span={8}>
              <DetailItem label="Rig name" value={wellData?.asset?.name} />
            </Col>
            <Col span={8}>
              <DetailItem
                label="Asset type"
                value={
                  wellData?.type
                    ? WELL_TYPE_NAME_MAP[wellData.type]
                    : wellData?.type
                }
              />
            </Col>
          </>
          <>
            <Col span={8}>
              <DetailItem label="Baseline" value={wellData?.baseline.name} />
            </Col>
            <Col span={8}>
              <DetailItem
                label="EMP"
                value={wellData?.emission_management_plan?.name}
              />
            </Col>
            <Col span={8}>
              <DetailDateItem
                label="Start date"
                value={
                  wellData?.actual_start_date || wellData?.planned_start_date
                }
              />
            </Col>
          </>
          <>
            <Col span={16}>
              <DetailItem
                label="Description:"
                layout="vertical"
                value={wellData?.description}
                gap={8}
                marginTop={10}
              />
            </Col>
          </>
        </Row>
      </DetailItemsProvider>
    </StyledModal>
  );
};

export default WellDetailsModal;
