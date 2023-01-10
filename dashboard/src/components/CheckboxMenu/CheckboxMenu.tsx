import { Checkbox } from 'antd';
import { StyledMenu } from './CheckboxMenu.styled';
import Box, { Flexbox } from 'components/Box';

export interface CheckboxMenuItemProps<T> {
  title: string;
  checked: boolean;
  key: T;
  color?: string;
}

export interface CheckboxMenuProps<T> {
  items: CheckboxMenuItemProps<T>[];
  onSelectAllChange: (checked: boolean) => void;
  onItemChange: (key: T, checked: boolean) => void;
  shadow?: boolean;
  minSelected?: number;
}

function CheckboxMenu<T>({
  items,
  onSelectAllChange,
  onItemChange,
  shadow,
  minSelected,
}: CheckboxMenuProps<T>) {
  const allChecked = items.every((item) => item.checked);
  const numChecked = items.filter((item) => item.checked).length;

  return (
    <StyledMenu width={192} shadow={shadow}>
      <StyledMenu.Item key="selectAll">
        <Checkbox
          checked={allChecked}
          disabled={allChecked && !!minSelected}
          onChange={(e) => onSelectAllChange(e.target.checked)}
        >
          Select all
        </Checkbox>
      </StyledMenu.Item>
      {items.map((item) => (
        <StyledMenu.Item key={String(item.key)}>
          <Flexbox
            gap={8}
            justifyContent="space-between"
            alignItems="center"
            width="100%"
          >
            <Checkbox
              checked={item.checked}
              disabled={
                item.checked && !!minSelected && numChecked === minSelected
              }
              onChange={(e) => onItemChange(item.key, e.target.checked)}
            >
              {item.title}
            </Checkbox>
            {item.color ? (
              <Box
                size={11}
                height={11}
                borderRadius="50%"
                backgroundColor={item.color}
                flexShrink={0}
              />
            ) : null}
          </Flexbox>
        </StyledMenu.Item>
      ))}
    </StyledMenu>
  );
}

export default CheckboxMenu;
