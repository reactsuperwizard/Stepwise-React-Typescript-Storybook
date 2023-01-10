import Menu from 'components/Menu';
import styled, { css } from 'styled-components';

export const StyledMenu = styled(Menu)<{ shadow?: boolean }>`
  border-radius: 8px;
  &.ant-menu-root.ant-menu-vertical {
    ${({ shadow }) =>
      shadow
        ? css`
            box-shadow: 0 4px 4px rgba(0, 0, 0, 0.05),
              0 6px 16px rgba(0, 0, 0, 0.08);
          `
        : undefined}
  }

  .ant-menu-item {
    height: 36px;
    line-height: 36px;
    margin-top: 0;
    margin-bottom: 0;
    padding: 0 14px;

    & .ant-menu-title-content {
      display: flex;
    }
    &:first-child {
      margin-top: 4px;
    }
    &:not(:last-child) {
      margin-bottom: 0;
    }
    &:last-child {
      margin-bottom: 14px;
    }

    .ant-checkbox + span {
      padding-right: 0;
    }
  }

  .ant-checkbox-wrapper {
    width: 100%;
    overflow: hidden;

    .ant-checkbox + span {
      font-size: 10px;
      line-height: 16px;
      width: 100%;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
  }
`;
