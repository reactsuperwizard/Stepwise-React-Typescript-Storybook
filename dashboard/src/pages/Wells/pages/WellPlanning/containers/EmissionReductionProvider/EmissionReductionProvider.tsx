import { MeasuredValue } from 'pages/Wells/consts';
import { createContext, Dispatch, useReducer } from 'react';
import useEmissionReductionInitiatives from 'pages/Wells/hooks/useEmissionReductionInitiatives';

interface EmissionReductionProviderProps {
  children: JSX.Element;
  wellPlanId: number;
}

export type State = {
  value: MeasuredValue;
  emissionReductionInitiatives: Record<string, boolean>;
  xLegend: 'days' | 'dates';
};

type Actions =
  | {
      type: 'selectEmissionReductionInitiatives';
      emissionReductionInitiatives: number[];
    }
  | {
      type: 'deselectEmissionReductionInitiatives';
      emissionReductionInitiatives: number[];
    }
  | {
      type: 'changeValue';
      value: MeasuredValue;
    }
  | {
      type: 'changeXLegend';
      xLegend: 'days' | 'dates';
    };

export const EmissionReductionProviderContext = createContext<
  [State, Dispatch<Actions>] | null
>(null);

function reducer(state: State, action: Actions) {
  switch (action.type) {
    case 'selectEmissionReductionInitiatives':
      return {
        ...state,
        emissionReductionInitiatives: Object.keys(
          state.emissionReductionInitiatives,
        ).reduce((accumulator, key) => {
          return {
            ...accumulator,
            [key]: action.emissionReductionInitiatives.includes(Number(key))
              ? true
              : state.emissionReductionInitiatives[key],
          };
        }, {}),
      };
    case 'deselectEmissionReductionInitiatives':
      return {
        ...state,
        emissionReductionInitiatives: Object.keys(
          state.emissionReductionInitiatives,
        ).reduce((accumulator, key) => {
          return {
            ...accumulator,
            [key]: action.emissionReductionInitiatives.includes(Number(key))
              ? false
              : state.emissionReductionInitiatives[key],
          };
        }, {}),
      };
    case 'changeValue':
      return {
        ...state,
        value: action.value,
      };
    case 'changeXLegend':
      return {
        ...state,
        xLegend: action.xLegend,
      };
    default:
      throw new Error('Unknown action');
  }
}

const EmissionReductionProvider = ({
  children,
  wellPlanId,
}: EmissionReductionProviderProps) => {
  const { baseloads, powerSystems } =
    useEmissionReductionInitiatives(wellPlanId);
  const initialState: State = {
    value: MeasuredValue.CO2,
    emissionReductionInitiatives: baseloads
      .concat(powerSystems)
      .reduce<Record<string, boolean>>((previousValue, currentValue) => {
        previousValue[currentValue.id] = true;
        return previousValue;
      }, {}),
    xLegend: 'days',
  };
  const [state, dispatch] = useReducer(reducer, initialState);

  return (
    <EmissionReductionProviderContext.Provider value={[state, dispatch]}>
      {children}
    </EmissionReductionProviderContext.Provider>
  );
};

export default EmissionReductionProvider;
