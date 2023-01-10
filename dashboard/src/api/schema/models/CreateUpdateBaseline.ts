/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { CreateUpdateBaselineSeason } from './CreateUpdateBaselineSeason';

export type CreateUpdateBaseline = {
    name: string;
    description: string;
    draft: boolean;
    /**
     * Boilers fuel consumption summer (m3 fuel/day)
     */
    boilers_fuel_consumption_summer: number;
    /**
     * Boilers fuel consumption winter (m3 fuel/day)
     */
    boilers_fuel_consumption_winter: number;
    summer: CreateUpdateBaselineSeason;
    winter: CreateUpdateBaselineSeason;
};
