from typing import NamedTuple

from apps.emissions.models import AssetType


class PhaseData(NamedTuple):
    name: str
    description: str
    transit: bool


class ModeData(NamedTuple):
    name: str
    description: str
    asset_types: tuple[AssetType, ...]
    transit: bool


INITIAL_CONCEPT_PHASES = (
    PhaseData('Transit', 'Transit phase', True),
    PhaseData('Positioning', 'Positioning phase', False),
    PhaseData('Top hole section', 'Top hole section phase', False),
    PhaseData('Transport section', 'Transport section phase', False),
    PhaseData('Reservoir section', 'Reservoir section phase', False),
    PhaseData('Completion', 'Completion phase', False),
    PhaseData('Well intervention', 'Well intervention phase', False),
    PhaseData('Plug and abandon', 'Plug and abandon phase', False),
    PhaseData('Waiting on weather', 'Waiting on weather phase', False),
    PhaseData('Downtime', 'Downtime phase', False),
)

INITIAL_CONCEPT_MODES = (
    ModeData(
        'Transit',
        'Transit mode',
        (AssetType.JACKUP, AssetType.FIXED_PLATFORM, AssetType.SEMI, AssetType.DRILLSHIP),
        True,
    ),
    ModeData('Fixed', 'Fixed mode', (AssetType.JACKUP, AssetType.FIXED_PLATFORM), False),
    ModeData('DP', 'DP mode', (AssetType.SEMI, AssetType.DRILLSHIP), False),
    ModeData('Poos Moor ATA', 'Poos Moor ATA mode', (AssetType.SEMI,), False),
)
