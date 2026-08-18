"""Result Fusion module exports."""

from fusion.fusion_service import FusionService
from fusion.models import FusionConfig
from fusion.deduplication import issues_are_duplicates

__all__ = ["FusionService", "FusionConfig", "issues_are_duplicates"]
