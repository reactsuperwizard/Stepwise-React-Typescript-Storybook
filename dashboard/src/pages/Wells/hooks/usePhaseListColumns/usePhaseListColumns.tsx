import { useMemo } from 'react';
import { Dropdown, MenuItemProps, Table } from 'antd';
import {
  WellPlannerDetailsCompleteStep,
  WellPlannerDetailsPlannedStep,
} from 'api/schema';
import { ColumnsType } from 'antd/lib/table/interface';
import { SEASON_NAME_MAP } from 'pages/WellPlan/consts';
import { prettyNumber, roundNumber } from 'utils/format';
import CheckMark from 'pages/Wells/components/CheckMark';
import { Flexbox } from 'components/Box';
import { notEmpty } from 'utils/data';
import useShowPhasesColumns, {
  PhaseListShowableColumns,
} from 'pages/Wells/hooks/useShowPhasesColumns';
import CheckboxMenu, { CheckboxMenuItemProps } from 'components/CheckboxMenu';
import Menu from 'components/Menu';
import Button from 'components/Button';
import { MoreOutlined, SettingOutlined } from '@ant-design/icons';
import { useTheme } from 'styled-components';

const usePhaseListColumns = <
  PhaseType extends
    | WellPlannerDetailsPlannedStep
    | WellPlannerDetailsCompleteStep,
>({
  selectionColumn,
  expandColumn,
  editable,
  onDeletePhase,
  onDuplicatePhase,
  onEditPhase,
  extraActions,
}: {
  selectionColumn: boolean;
  expandColumn: boolean;
  editable: boolean;
  onDeletePhase: (phase: PhaseType) => void;
  onDuplicatePhase: (phase: PhaseType) => void;
  onEditPhase: (phaseId: number) => void;
  extraActions?: {
    key: string;
    menuItemProps: (phase: PhaseType) => MenuItemProps;
  }[];
}) => {
  const { colors } = useTheme();
  const {
    onSelectColumn,
    onSelectAllColumns,
    values: columnValues,
  } = useShowPhasesColumns();
  const selectableColumns: CheckboxMenuItemProps<
    keyof PhaseListShowableColumns
  >[] = useMemo(
    () => [
      { title: 'Phase', checked: columnValues.phase, key: 'phase' },
      {
        title: 'Section length (m)',
        checked: columnValues.sectionLength,
        key: 'sectionLength',
      },
      {
        title: 'Mode',
        checked: columnValues.mode,
        key: 'mode',
      },
      { title: 'Season', checked: columnValues.season, key: 'season' },
      { title: 'Duration', checked: columnValues.duration, key: 'duration' },
      {
        title: 'Waiting on weather (%)',
        checked: columnValues.waitingOnWeather,
        key: 'waitingOnWeather',
      },
      {
        title: 'External supply',
        checked: columnValues.externalEnergySupplyEnabled,
        key: 'externalEnergySupplyEnabled',
      },
      {
        title: 'External supply quota',
        checked: columnValues.externalEnergySupplyQuota,
        key: 'externalEnergySupplyQuota',
      },
      {
        title: 'CC&S',
        checked: columnValues.carbonCaptureStorageSystemQuantity,
        key: 'carbonCaptureStorageSystemQuantity',
      },
      {
        title: 'Materials',
        checked: columnValues.materials,
        key: 'materials',
      },
      {
        title: 'ERIs',
        checked: columnValues.emissionReductionInitiatives,
        key: 'emissionReductionInitiatives',
      },
      {
        title: 'Comment',
        checked: columnValues.comment,
        key: 'comment',
      },
    ],
    [columnValues],
  );
  const columns: ColumnsType<PhaseType> = useMemo(() => {
    return [
      selectionColumn ? Table.SELECTION_COLUMN : undefined,
      expandColumn ? Table.EXPAND_COLUMN : undefined,
    ]
      .filter(notEmpty)
      .concat(
        [
          {
            title: 'Phase',
            dataIndex: 'phase',
            width: 120,
            show: columnValues.phase,
            render: (phase: PhaseType['phase']) => phase.name,
          },
          {
            title: 'Section length (m)',
            dataIndex: 'well_section_length',
            width: 150,
            show: columnValues.sectionLength,
            render: (sectionLength: PhaseType['well_section_length']) =>
              sectionLength ? sectionLength : undefined,
          },
          {
            title: 'Mode',
            dataIndex: 'mode',
            width: 120,
            show: columnValues.mode,
            render: (mode: PhaseType['mode']) => mode.name,
          },
          {
            title: 'Season',
            dataIndex: 'season',
            width: 80,
            show: columnValues.season,
            render: (season: PhaseType['season']) => SEASON_NAME_MAP[season],
          },
          {
            title: 'Duration',
            dataIndex: 'duration',
            width: 70,
            show: columnValues.duration,
            render: (duration: PhaseType['duration']) =>
              prettyNumber(roundNumber(duration, 2)),
          },
          {
            title: 'Waiting on weather (%)',
            dataIndex: 'waiting_on_weather',
            width: 170,
            show: columnValues.waitingOnWeather,
            render: (value: PhaseType['waiting_on_weather']) => {
              return `${value}%`;
            },
          },
          {
            title: 'External supply',
            dataIndex: 'external_energy_supply_enabled',
            width: 120,
            show: columnValues.externalEnergySupplyEnabled,
            render: (
              externalEnergySupplyEnabled: PhaseType['external_energy_supply_enabled'],
            ) => (
              <Flexbox justifyContent="center">
                <CheckMark checked={externalEnergySupplyEnabled} />
              </Flexbox>
            ),
          },
          {
            title: 'External supply quota',
            dataIndex: 'external_energy_supply_quota',
            width: 160,
            show: columnValues.externalEnergySupplyQuota,
            render: (
              externalEnergySupplyQuota: PhaseType['external_energy_supply_quota'],
            ) => (
              <Flexbox justifyContent="center">
                <CheckMark checked={externalEnergySupplyQuota} />
              </Flexbox>
            ),
          },
          {
            title: 'CC&S',
            dataIndex: 'carbon_capture_storage_system_quantity',
            width: 50,
            show: columnValues.carbonCaptureStorageSystemQuantity,
            render: (
              carbonCaptureStorageSystemQuantity: PhaseType['carbon_capture_storage_system_quantity'],
            ) => (
              <Flexbox justifyContent="center">
                <CheckMark checked={!!carbonCaptureStorageSystemQuantity} />
              </Flexbox>
            ),
          },
          {
            title: 'Materials',
            dataIndex: 'materials',
            show: columnValues.materials,
            width: 90,
            render: (materials: PhaseType['materials']) => (
              <Flexbox justifyContent="center">
                <CheckMark checked={!!materials.length} />
              </Flexbox>
            ),
          },
          {
            title: 'ERIs',
            dataIndex: 'emission_reduction_initiatives',
            show: columnValues.emissionReductionInitiatives,
            width: 90,
            render: (
              emissionReductionInitiatives: PhaseType['emission_reduction_initiatives'],
            ) => (
              <Flexbox justifyContent="center">
                <CheckMark checked={!!emissionReductionInitiatives.length} />
              </Flexbox>
            ),
          },
          {
            title: 'Comment',
            dataIndex: 'comment',
            width: 340,
            show: columnValues.comment,
          },
          {
            title: '',
            key: 'actions',
            className: 'ant-table-cell-actions ant-table-column-choose-columns',
            width: 48,
            show: true,
            filterDropdown: () => {
              return (
                <CheckboxMenu
                  items={selectableColumns}
                  onItemChange={onSelectColumn}
                  onSelectAllChange={onSelectAllColumns}
                  minSelected={1}
                />
              );
            },
            filterIcon: () => (
              <SettingOutlined
                style={{ color: colors.text.primary, fontSize: 16 }}
              />
            ),
            render: (phase: PhaseType) => {
              const menu = (
                <Menu width={181}>
                  <Menu.Item
                    key="edit"
                    onClick={() => onEditPhase(phase.id)}
                    disabled={!editable}
                  >
                    Edit
                  </Menu.Item>
                  <Menu.Item
                    key="duplicate"
                    onClick={() => onDuplicatePhase(phase)}
                    disabled={!editable}
                  >
                    Duplicate
                  </Menu.Item>
                  {extraActions?.map((action) => (
                    <Menu.Item
                      key={action.key}
                      {...action.menuItemProps(phase)}
                    />
                  ))}
                  <Menu.Item
                    key="delete"
                    onClick={() => onDeletePhase(phase)}
                    disabled={!editable}
                  >
                    Delete
                  </Menu.Item>
                </Menu>
              );
              return (
                <Dropdown overlay={menu} trigger={['click']}>
                  <Button type="link" icon={<MoreOutlined />} />
                </Dropdown>
              );
            },
          },
        ].filter((column) => column.show || column.show === undefined),
      );
  }, [
    selectionColumn,
    expandColumn,
    columnValues,
    selectableColumns,
    onSelectColumn,
    onSelectAllColumns,
    colors.text.primary,
    editable,
    extraActions,
    onEditPhase,
    onDuplicatePhase,
    onDeletePhase,
  ]);

  return columns;
};

export default usePhaseListColumns;
