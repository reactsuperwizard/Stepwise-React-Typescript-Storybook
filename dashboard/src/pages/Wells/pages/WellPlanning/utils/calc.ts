import { WellCO2Emission } from 'api/schema';

export const calculateTotalCO2Emission = ({
  data,
  scopes: { scope1, scope2, scope3 },
}: {
  scopes: {
    scope1: boolean;
    scope2: boolean;
    scope3: boolean;
  };
  data: WellCO2Emission;
}) => {
  return (
    Number(scope1) * (data.asset + data.boilers) +
    Number(scope2) * data.external_energy_supply +
    Number(scope3) * (data.vessels + data.helicopters + data.materials)
  );
};
