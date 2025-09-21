"""
PCS (PSD Convention Standard) data models.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class PCSTag:
    """Represents a parsed PCS tag from layer names."""

    group: Optional[str] = None
    part: Optional[str] = None
    side: Optional[str] = None
    state: Optional[str] = None
    viseme: Optional[str] = None
    emotion: Optional[str] = None
    shape: Optional[str] = None
    variant: Optional[str] = None
    layer: Optional[str] = None
    turn: Optional[str] = None
    blush: Optional[str] = None
    custom: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_string(cls, tag_string: str) -> "PCSTag":
        """Parse PCS tag from string like '[group=Face part=Eye side=L state=open]'."""
        tag = cls()

        # Remove brackets and split by spaces
        if tag_string.startswith("[") and tag_string.endswith("]"):
            tag_string = tag_string[1:-1]

        for token in tag_string.split():
            if "=" in token:
                key, value = token.split("=", 1)
                key = key.strip().lower()
                value = value.strip()

                # Map to known attributes
                if hasattr(tag, key):
                    setattr(tag, key, value)
                else:
                    tag.custom[key] = value

        return tag

    def to_slot_key(self) -> str:
        """Generate a standardized slot key for this tag."""
        parts = []

        if self.part:
            parts.append(self.part)
        if self.side:
            parts.append(self.side)

        return "".join(parts) if parts else "Unknown"

    def to_state_key(self) -> str:
        """Generate a standardized state key for this tag."""
        if self.viseme:
            return f"viseme/{self.viseme}"
        elif self.emotion:
            return f"emotion/{self.emotion}"
        elif self.state:
            return f"state/{self.state}"
        elif self.shape:
            return f"shape/{self.shape}"
        else:
            return "default"


@dataclass
class LayerInfo:
    """Information about a PSD layer."""

    name: str
    index: int
    path: List[str]  # Ancestry path from root
    visible: bool
    bbox: Tuple[int, int, int, int]  # (left, top, right, bottom)
    blend_mode: str
    pcs_tag: Optional[PCSTag] = None
    base_name: str = ""

    def __post_init__(self):
        """Parse PCS tag from layer name if present."""
        self.base_name, self.pcs_tag = self._parse_layer_name(self.name)

    @staticmethod
    def _parse_layer_name(name: str) -> Tuple[str, Optional[PCSTag]]:
        """Parse layer name into base name and PCS tag."""
        import re

        # Look for PCS tag pattern: [key=value key=value ...]
        tag_pattern = r"\[([^\]]+)\]"
        match = re.search(tag_pattern, name)

        if match:
            tag_string = match.group(0)
            base_name = name.replace(tag_string, "").strip()
            pcs_tag = PCSTag.from_string(tag_string)
            return base_name, pcs_tag
        else:
            return name, None


@dataclass
class MappingRule:
    """A rule for mapping layer names to PCS tags."""

    match_pattern: str  # Regex pattern
    mapping: Dict[str, str]  # Key-value pairs to apply
    priority: int = 0  # Higher priority rules are applied first

    def matches(self, layer_name: str) -> bool:
        """Check if this rule matches the given layer name."""
        import re

        try:
            return bool(re.search(self.match_pattern, layer_name, re.IGNORECASE))
        except re.error:
            return False

    def apply(self, layer_info: LayerInfo) -> PCSTag:
        """Apply this rule to create or modify a PCS tag."""
        if layer_info.pcs_tag:
            tag = layer_info.pcs_tag
        else:
            tag = PCSTag()

        for key, value in self.mapping.items():
            if hasattr(tag, key):
                setattr(tag, key, value)
            else:
                tag.custom[key] = value

        return tag


@dataclass
class FolderRule:
    """A rule for mapping folder paths to PCS attributes."""

    path_pattern: str
    mapping: Dict[str, str]

    def matches(self, layer_path: List[str]) -> bool:
        """Check if this rule matches the given layer path."""
        path_str = "/".join(layer_path)
        return self.path_pattern.lower() in path_str.lower()

    def apply(self, layer_info: LayerInfo) -> PCSTag:
        """Apply this rule to create or modify a PCS tag."""
        if layer_info.pcs_tag:
            tag = layer_info.pcs_tag
        else:
            tag = PCSTag()

        for key, value in self.mapping.items():
            if hasattr(tag, key):
                setattr(tag, key, value)
            else:
                tag.custom[key] = value

        return tag
