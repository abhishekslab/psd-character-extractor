"""
Avatar bundle data models.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class AnchorPoint:
    """Represents an anchor point in the avatar."""

    x: float
    y: float


@dataclass
class SliceRect:
    """Represents a sprite slice in the atlas."""

    x: int
    y: int
    w: int
    h: int


@dataclass
class SlotDefinition:
    """Defines a slot that can hold different states/expressions."""

    states: Optional[List[str]] = None
    visemes: Optional[List[str]] = None
    emotions: Optional[List[str]] = None
    shapes: Optional[List[str]] = None


@dataclass
class AvatarMeta:
    """Avatar metadata."""

    name: str
    source: str
    generator: str = "psd-character-extractor"


@dataclass
class AvatarImages:
    """Avatar image assets."""

    atlas: str
    slices: Dict[str, SliceRect] = field(default_factory=dict)


@dataclass
class AvatarBundle:
    """Complete avatar bundle data structure."""

    schema: str = "./schemas/avatar.schema.json"
    meta: Optional[AvatarMeta] = None
    images: Optional[AvatarImages] = None
    slots: Dict[str, SlotDefinition] = field(default_factory=dict)
    anchors: Dict[str, AnchorPoint] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {"$schema": self.schema}

        if self.meta:
            result["meta"] = {
                "name": self.meta.name,
                "source": self.meta.source,
                "generator": self.meta.generator,
            }

        if self.images:
            result["images"] = {
                "atlas": self.images.atlas,
                "slices": {
                    key: {"x": rect.x, "y": rect.y, "w": rect.w, "h": rect.h}
                    for key, rect in self.images.slices.items()
                },
            }

        result["slots"] = {}
        for slot_name, slot_def in self.slots.items():
            slot_dict = {}
            if slot_def.states:
                slot_dict["states"] = slot_def.states
            if slot_def.visemes:
                slot_dict["visemes"] = slot_def.visemes
            if slot_def.emotions:
                slot_dict["emotions"] = slot_def.emotions
            if slot_def.shapes:
                slot_dict["shapes"] = slot_def.shapes
            result["slots"][slot_name] = slot_dict

        result["anchors"] = {
            name: {"x": anchor.x, "y": anchor.y}
            for name, anchor in self.anchors.items()
        }

        return result
