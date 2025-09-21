"""
Auto Mapper with Rule Engine

Maps PSD layers to avatar slots using configurable rules and heuristics.
"""

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from .models.avatar import (
    AnchorPoint,
    AvatarBundle,
    AvatarImages,
    AvatarMeta,
    SlotDefinition,
)
from .models.pcs import FolderRule, LayerInfo, MappingRule, PCSTag

logger = logging.getLogger(__name__)


class AutoMapper:
    """Maps PSD layers to avatar slots using rule-driven inference."""

    # Default viseme mapping for lipsync
    DEFAULT_VISEMES = ["SIL", "AI", "E", "U", "O", "FV", "L", "WQ", "MBP", "REST"]

    # Default emotion mapping
    DEFAULT_EMOTIONS = ["neutral", "smile", "frown", "joy", "sad", "angry"]

    # Default eye states
    DEFAULT_EYE_STATES = ["open", "half", "closed", "happy", "sad", "angry", "wink"]

    # Default brow shapes
    DEFAULT_BROW_SHAPES = ["neutral", "up", "down", "angry", "sad"]

    def __init__(self, rules_file: Optional[str] = None):
        """
        Initialize the auto mapper.

        Args:
            rules_file: Path to YAML rules file (optional)
        """
        self.mapping_rules: List[MappingRule] = []
        self.folder_rules: List[FolderRule] = []
        self.language_pack: Dict[str, str] = {}

        if rules_file:
            self.load_rules(rules_file)
        else:
            self._load_default_rules()

    def load_rules(self, rules_file: str) -> None:
        """
        Load mapping rules from YAML file.

        Args:
            rules_file: Path to the YAML rules file
        """
        try:
            with open(rules_file, "r", encoding="utf-8") as f:
                rules_data = yaml.safe_load(f)

            self._parse_rules(rules_data)
            logger.info(
                f"Loaded {len(self.mapping_rules)} mapping rules and {len(self.folder_rules)} folder rules"
            )

        except Exception as e:
            logger.error(f"Failed to load rules file {rules_file}: {e}")
            self._load_default_rules()

    def _load_default_rules(self) -> None:
        """Load default mapping rules."""
        default_rules = {
            "aliases": [
                {
                    "match": r"(?i)eye[_ -]?l.*open",
                    "map": {
                        "group": "Face",
                        "part": "Eye",
                        "side": "L",
                        "state": "open",
                    },
                },
                {
                    "match": r"(?i)eye[_ -]?l.*closed",
                    "map": {
                        "group": "Face",
                        "part": "Eye",
                        "side": "L",
                        "state": "closed",
                    },
                },
                {
                    "match": r"(?i)eye[_ -]?l.*half",
                    "map": {
                        "group": "Face",
                        "part": "Eye",
                        "side": "L",
                        "state": "half",
                    },
                },
                {
                    "match": r"(?i)eye[_ -]?r.*open",
                    "map": {
                        "group": "Face",
                        "part": "Eye",
                        "side": "R",
                        "state": "open",
                    },
                },
                {
                    "match": r"(?i)eye[_ -]?r.*closed",
                    "map": {
                        "group": "Face",
                        "part": "Eye",
                        "side": "R",
                        "state": "closed",
                    },
                },
                {
                    "match": r"(?i)eye[_ -]?r.*half",
                    "map": {
                        "group": "Face",
                        "part": "Eye",
                        "side": "R",
                        "state": "half",
                    },
                },
                {
                    "match": r"(?i)mouth[_ -]?(mbp|m|b|p)",
                    "map": {"group": "Face", "part": "Mouth", "viseme": "MBP"},
                },
                {
                    "match": r"(?i)mouth[_ -]?a(i)?",
                    "map": {"group": "Face", "part": "Mouth", "viseme": "AI"},
                },
                {
                    "match": r"(?i)mouth[_ -]?e",
                    "map": {"group": "Face", "part": "Mouth", "viseme": "E"},
                },
                {
                    "match": r"(?i)mouth[_ -]?u",
                    "map": {"group": "Face", "part": "Mouth", "viseme": "U"},
                },
                {
                    "match": r"(?i)mouth[_ -]?o",
                    "map": {"group": "Face", "part": "Mouth", "viseme": "O"},
                },
                {
                    "match": r"(?i)mouth[_ -]?(rest|closed|normal)",
                    "map": {"group": "Face", "part": "Mouth", "viseme": "REST"},
                },
                {
                    "match": r"(?i)brow[_ -]?l",
                    "map": {
                        "group": "Face",
                        "part": "Brow",
                        "side": "L",
                        "shape": "neutral",
                    },
                },
                {
                    "match": r"(?i)brow[_ -]?r",
                    "map": {
                        "group": "Face",
                        "part": "Brow",
                        "side": "R",
                        "shape": "neutral",
                    },
                },
            ],
            "folders": [
                {
                    "path": "Face/Eyes/L",
                    "map": {"group": "Face", "part": "Eye", "side": "L"},
                },
                {
                    "path": "Face/Eyes/R",
                    "map": {"group": "Face", "part": "Eye", "side": "R"},
                },
                {"path": "Face/Mouth", "map": {"group": "Face", "part": "Mouth"}},
                {"path": "Face/Brows", "map": {"group": "Face", "part": "Brow"}},
            ],
        }

        self._parse_rules(default_rules)

    def _parse_rules(self, rules_data: Dict[str, Any]) -> None:
        """Parse rules from loaded YAML data."""
        # Parse alias rules
        for alias in rules_data.get("aliases", []):
            rule = MappingRule(
                match_pattern=alias["match"],
                mapping=alias["map"],
                priority=alias.get("priority", 0),
            )
            self.mapping_rules.append(rule)

        # Sort by priority (higher first)
        self.mapping_rules.sort(key=lambda r: r.priority, reverse=True)

        # Parse folder rules
        for folder in rules_data.get("folders", []):
            rule = FolderRule(path_pattern=folder["path"], mapping=folder["map"])
            self.folder_rules.append(rule)

        # Load language pack if present
        self.language_pack = rules_data.get("language_pack", {})

    def map_layers(self, layers: List[LayerInfo]) -> AvatarBundle:
        """
        Map PSD layers to avatar bundle using rules and heuristics.

        Args:
            layers: List of scanned layer information

        Returns:
            AvatarBundle with mapped slots and metadata
        """
        avatar = AvatarBundle()

        # Apply mapping rules to enhance PCS tags
        enhanced_layers = self._apply_mapping_rules(layers)

        # Group layers by slots
        slot_groups = self._group_layers_by_slot(enhanced_layers)

        # Build slot definitions
        avatar.slots = self._build_slot_definitions(slot_groups)

        # Set up basic metadata
        avatar.meta = AvatarMeta(
            name="Generated Avatar",
            source="PSD File",
            generator="psd-character-extractor",
        )

        # Add default anchor points
        avatar.anchors = {"headPivot": AnchorPoint(x=256, y=128)}

        logger.info(
            f"Mapped {len(enhanced_layers)} layers to {len(avatar.slots)} slots"
        )
        return avatar

    def _apply_mapping_rules(self, layers: List[LayerInfo]) -> List[LayerInfo]:
        """Apply mapping rules to enhance layer PCS tags."""
        enhanced_layers = []

        for layer in layers:
            enhanced_layer = layer
            applied_rule = False

            # First, try explicit PCS tags (already parsed)
            if layer.pcs_tag:
                enhanced_layers.append(enhanced_layer)
                continue

            # Apply regex alias rules
            for rule in self.mapping_rules:
                if rule.matches(layer.name):
                    enhanced_layer.pcs_tag = rule.apply(layer)
                    applied_rule = True
                    logger.debug(
                        f"Applied alias rule to '{layer.name}': {rule.mapping}"
                    )
                    break

            # Apply folder rules if no alias rule matched
            if not applied_rule:
                for folder_rule in self.folder_rules:
                    if folder_rule.matches(layer.path):
                        enhanced_layer.pcs_tag = folder_rule.apply(layer)
                        applied_rule = True
                        logger.debug(
                            f"Applied folder rule to '{layer.name}': {folder_rule.mapping}"
                        )
                        break

            # Apply language pack translations
            if enhanced_layer.pcs_tag and enhanced_layer.pcs_tag.viseme:
                viseme = enhanced_layer.pcs_tag.viseme
                if viseme in self.language_pack:
                    enhanced_layer.pcs_tag.viseme = self.language_pack[viseme]

            enhanced_layers.append(enhanced_layer)

        return enhanced_layers

    def _group_layers_by_slot(
        self, layers: List[LayerInfo]
    ) -> Dict[str, List[LayerInfo]]:
        """Group layers by their target slot."""
        slot_groups = {}

        for layer in layers:
            if not layer.pcs_tag:
                continue

            slot_key = layer.pcs_tag.to_slot_key()
            if slot_key not in slot_groups:
                slot_groups[slot_key] = []

            slot_groups[slot_key].append(layer)

        return slot_groups

    def _build_slot_definitions(
        self, slot_groups: Dict[str, List[LayerInfo]]
    ) -> Dict[str, SlotDefinition]:
        """Build slot definitions from grouped layers."""
        slots = {}

        for slot_name, slot_layers in slot_groups.items():
            slot_def = SlotDefinition()

            # Collect unique values for each attribute
            visemes = set()
            emotions = set()
            states = set()
            shapes = set()

            for layer in slot_layers:
                if layer.pcs_tag:
                    if layer.pcs_tag.viseme:
                        visemes.add(layer.pcs_tag.viseme)
                    if layer.pcs_tag.emotion:
                        emotions.add(layer.pcs_tag.emotion)
                    if layer.pcs_tag.state:
                        states.add(layer.pcs_tag.state)
                    if layer.pcs_tag.shape:
                        shapes.add(layer.pcs_tag.shape)

            # Set slot definition attributes
            if visemes:
                slot_def.visemes = sorted(list(visemes))
            if emotions:
                slot_def.emotions = sorted(list(emotions))
            if states:
                slot_def.states = sorted(list(states))
            if shapes:
                slot_def.shapes = sorted(list(shapes))

            # Set defaults for standard slots
            if slot_name.startswith("Eye"):
                if not slot_def.states:
                    slot_def.states = self.DEFAULT_EYE_STATES
            elif slot_name.startswith("Brow"):
                if not slot_def.shapes:
                    slot_def.shapes = self.DEFAULT_BROW_SHAPES
            elif slot_name == "Mouth":
                if not slot_def.visemes:
                    slot_def.visemes = self.DEFAULT_VISEMES
                if not slot_def.emotions:
                    slot_def.emotions = self.DEFAULT_EMOTIONS

            slots[slot_name] = slot_def

        return slots

    def generate_mapping_report(
        self, layers: List[LayerInfo], avatar: AvatarBundle
    ) -> Dict[str, Any]:
        """
        Generate a mapping report with warnings and statistics.

        Args:
            layers: Original layer list
            avatar: Generated avatar bundle

        Returns:
            Dictionary containing mapping report
        """
        report = {
            "summary": {
                "total_layers": len(layers),
                "mapped_layers": 0,
                "unmapped_layers": 0,
                "slots_created": len(avatar.slots),
            },
            "warnings": [],
            "coverage": {},
            "unmapped_layers": [],
        }

        # Count mapped/unmapped layers
        for layer in layers:
            if layer.pcs_tag:
                report["summary"]["mapped_layers"] += 1
            else:
                report["summary"]["unmapped_layers"] += 1
                report["unmapped_layers"].append(layer.name)

        # Check coverage for essential slots
        essential_slots = ["EyeL", "EyeR", "Mouth"]
        for slot in essential_slots:
            if slot not in avatar.slots:
                report["warnings"].append(f"Missing essential slot: {slot}")
            else:
                slot_def = avatar.slots[slot]
                coverage = {}

                if slot.startswith("Eye"):
                    required_states = ["open", "closed"]
                    available_states = slot_def.states or []
                    missing_states = [
                        s for s in required_states if s not in available_states
                    ]
                    if missing_states:
                        report["warnings"].append(
                            f"Slot {slot} missing states: {missing_states}"
                        )
                    coverage["states"] = available_states

                elif slot == "Mouth":
                    required_visemes = ["REST", "AI", "E", "U", "O"]
                    available_visemes = slot_def.visemes or []
                    missing_visemes = [
                        v for v in required_visemes if v not in available_visemes
                    ]
                    if missing_visemes:
                        report["warnings"].append(
                            f"Slot {slot} missing visemes: {missing_visemes}"
                        )
                    coverage["visemes"] = available_visemes

                report["coverage"][slot] = coverage

        return report
