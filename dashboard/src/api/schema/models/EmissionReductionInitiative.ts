/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { EmissionReductionInitiativeTypeEnum } from './EmissionReductionInitiativeTypeEnum';

export type EmissionReductionInitiative = {
    id: number;
    type: EmissionReductionInitiativeTypeEnum;
    name: string;
    value: number;
};
