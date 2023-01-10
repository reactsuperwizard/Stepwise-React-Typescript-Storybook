import styled from 'styled-components';

export const Tooltip = styled.div<{ xOverflow?: boolean; width: number }>`
  background-color: ${({ theme }) => theme.colors.white};
  padding: 15px;
  border-radius: 2px;
  filter: drop-shadow(0px 4px 4px rgba(0, 0, 0, 0.05))
    drop-shadow(0px 6px 16px rgba(0, 0, 0, 0.08));
  width: ${({ width }) => `${width}px`};

  &:after {
    content: '';
    position: absolute;
    top: -12px;
    left: ${({ xOverflow }) => (xOverflow ? '93%' : '50%')};
    transform: rotate(180deg);
    margin-left: -7px;
    border-width: 7px;
    border-style: solid;
    border-color: ${({ theme }) => theme.colors.white} transparent transparent
      transparent;
  }
`;
