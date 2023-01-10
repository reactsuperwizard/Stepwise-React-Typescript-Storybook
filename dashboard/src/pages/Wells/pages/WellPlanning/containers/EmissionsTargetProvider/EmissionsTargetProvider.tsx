import { MeasuredValue } from 'pages/Wells/consts';
import { createContext, Dispatch, useReducer } from 'react';

interface EmissionsTargetProviderProps {
  children: JSX.Element;
}

export type State = {
  value: MeasuredValue;
  scopes: {
    scope1: boolean;
    scope2: boolean;
    scope3: boolean;
  };
  lines: {
    baseline: boolean;
    target: boolean;
  };
  xLegend: 'days' | 'dates';
};

type Actions =
  | { type: 'toggleScope'; scope: 'scope1' | 'scope2' | 'scope3' }
  | { type: 'toggleLine'; line: 'baseline' | 'target' }
  | {
      type: 'changeValue';
      value: MeasuredValue;
    }
  | {
      type: 'changeXLegend';
      xLegend: 'days' | 'dates';
    };

export const EmissionsTargetProviderContext = createContext<
  [State, Dispatch<Actions>] | null
>(null);

function reducer(state: State, action: Actions) {
  switch (action.type) {
    case 'toggleScope':
      return {
        ...state,
        scopes: {
          ...state.scopes,
          [action.scope]: !state.scopes[action.scope],
        },
      };
    case 'toggleLine':
      return {
        ...state,
        lines: {
          ...state.lines,
          [action.line]: !state.lines[action.line],
        },
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

const initialState: State = {
  value: MeasuredValue.CO2,
  scopes: {
    scope1: true,
    scope2: true,
    scope3: true,
  },
  lines: {
    baseline: true,
    target: true,
  },
  xLegend: 'days',
};

const EmissionsTargetProvider = ({
  children,
}: EmissionsTargetProviderProps) => {
  const [state, dispatch] = useReducer(reducer, initialState);

  return (
    <EmissionsTargetProviderContext.Provider value={[state, dispatch]}>
      {children}
    </EmissionsTargetProviderContext.Provider>
  );
};

export default EmissionsTargetProvider;
