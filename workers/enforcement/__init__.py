"""
Worker Enforcement Module (R13.4)

Provides automatic constraint enforcement for worker instances:
- WitnessRegistry: Registry of witness verification functions
- WitnessEnforcement: Automatic constraint verification platform
"""

from workers.enforcement.registry import WitnessRegistry
from workers.enforcement.witness import WitnessEnforcement

__all__ = ["WitnessRegistry", "WitnessEnforcement"]
