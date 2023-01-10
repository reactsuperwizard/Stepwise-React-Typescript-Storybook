import { Button } from 'antd';
import styled from 'styled-components';

export const DropdownButton = styled(Button)`
  height: 26px;
  padding: 5px 16px;
  font-weight: 400;
  font-size: 10px;
  line-height: 16px;
  color: ${({ theme }) => theme.colors.gray[6]};
  background-color: ${({ theme }) => theme.colors.gray[2]};
  border-color: ${({ theme }) => theme.colors.gray[5]};

  &.ant-btn:hover,
  &.ant-btn:focus,
  &.ant-btn:active {
    background-color: ${({ theme }) => theme.colors.gray[2]};
  }
`;
