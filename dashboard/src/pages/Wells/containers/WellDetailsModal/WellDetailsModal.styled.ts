import { Modal } from 'antd';
import styled from 'styled-components';

export const StyledModal = styled(Modal)`
  .ant-modal-header {
    border-bottom: 0 none;
    padding: 81px 64px 0;

    .ant-modal-title {
      font-size: 20px;
      line-height: 28px;
      font-weight: 600;
    }
  }

  .ant-modal-body {
    padding: 35px 64px 81px;
  }

  .ant-modal-close-x {
    height: 94px;
    width: 98px;
    line-height: 94px;
  }
`;
