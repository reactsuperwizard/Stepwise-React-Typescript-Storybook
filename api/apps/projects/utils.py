from typing import TypedDict

from apps.rigs.models import CustomDrillship, CustomJackupRig, CustomSemiRig, RigType


class GenericRigData(TypedDict):
    id: int
    type: RigType


def get_rig_model(rig_type: RigType) -> type[CustomSemiRig] | type[CustomJackupRig] | type[CustomDrillship]:
    if rig_type == RigType.SEMI:
        return CustomSemiRig
    elif rig_type == RigType.JACKUP:
        return CustomJackupRig
    elif rig_type == RigType.DRILLSHIP:
        return CustomDrillship
    raise ValueError(f'Unknown rig type: {rig_type}')
