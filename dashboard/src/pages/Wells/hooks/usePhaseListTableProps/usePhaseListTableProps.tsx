import { DownOutlined, UpOutlined } from '@ant-design/icons';
import {
  WellPlannerDetailsCompleteStep,
  WellPlannerDetailsPlannedStep,
} from 'api/schema';
import { ExpandedRowRender } from 'rc-table/lib/interface';
import { TableProps } from 'antd';
import React from 'react';
import {
  DroppableTableBody,
  DraggableTableRow,
} from 'pages/Wells/components/PhaseTable';
import { DraggableTableCell } from 'components/DraggableTable';

interface UsePhaseListTableProps<
  PhaseType extends
    | WellPlannerDetailsPlannedStep
    | WellPlannerDetailsCompleteStep,
> {
  selectedRowKeys: number[];
  expandable: boolean;
  expandedRowRender?: ExpandedRowRender<PhaseType>;
  rowSelection?: boolean;
  editable: boolean;
  setSelectedPhases: (selectedRows: number[]) => void;
}

const usePhaseListTableProps = <
  PhaseType extends
    | WellPlannerDetailsPlannedStep
    | WellPlannerDetailsCompleteStep,
>({
  selectedRowKeys,
  expandedRowRender,
  expandable,
  rowSelection,
  editable,
  setSelectedPhases,
}: UsePhaseListTableProps<PhaseType>): TableProps<PhaseType> => {
  return {
    pagination: false,
    locale: {
      emptyText: 'No phase added',
    },
    expandable: expandable
      ? {
          expandIcon: ({ record, expanded, onExpand }) =>
            expanded ? (
              <UpOutlined onClick={(event) => onExpand(record, event)} />
            ) : (
              <DownOutlined onClick={(event) => onExpand(record, event)} />
            ),
          expandedRowRender,
        }
      : undefined,
    rowSelection: rowSelection
      ? {
          type: 'checkbox',
          selectedRowKeys,
          onChange: (rowKeysSelected: (string | number)[]) => {
            setSelectedPhases(rowKeysSelected.map(Number));
          },
        }
      : undefined,
    rowClassName: (phase) => {
      if ('approved' in phase && phase.approved) {
        return 'ant-table-row-active';
      }
      return '';
    },
    onRow: (phase, index) => {
      const attr = {
        index,
        draggableId: phase.id,
      };
      return attr as React.HTMLAttributes<unknown>;
    },
    components: editable
      ? {
          body: {
            wrapper: DroppableTableBody,
            row: DraggableTableRow,
            cell: DraggableTableCell,
          },
        }
      : undefined,
    className: 'ant-table-with-actions',
    rowKey: (phase) => phase.id,
  };
};

export default usePhaseListTableProps;
