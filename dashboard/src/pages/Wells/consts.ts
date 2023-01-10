import { WellPlannerWellTypeEnum } from 'api/schema';

export const WELL_TYPE_NAME_MAP: Record<WellPlannerWellTypeEnum, string> = {
  [WellPlannerWellTypeEnum.EXPLORATION]: 'Exploration',
  [WellPlannerWellTypeEnum.PRODUCTION]: 'Production',
  [WellPlannerWellTypeEnum.APPRAISAL]: 'Appraisal',
};

export enum MeasuredValue {
  CO2 = 'CO2',
  NOx = 'NOx',
  Fuel = 'Fuel',
  FuelCost = 'FuelCost',
}
