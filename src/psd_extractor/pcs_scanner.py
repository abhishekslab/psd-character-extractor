"""
PCS (PSD Convention Standard) Scanner

Scans PSD files and extracts layer information according to the PCS specification.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from psd_tools import PSDImage
from psd_tools.api.layers import Group, Layer

from .models.pcs import LayerInfo, PCSTag

logger = logging.getLogger(__name__)


class PCSScanner:
    """Scans PSD files and extracts layer information with PCS tag parsing."""

    def __init__(self, psd_path: str):
        """
        Initialize the PCS scanner.

        Args:
            psd_path: Path to the PSD file
        """
        self.psd_path = psd_path
        self.psd: Optional[PSDImage] = None
        self._load_psd()

    def _load_psd(self) -> None:
        """Load the PSD file."""
        try:
            self.psd = PSDImage.open(self.psd_path)
            logger.info(f"Loaded PSD file for scanning: {self.psd_path}")
        except Exception as e:
            logger.error(f"Failed to load PSD file: {e}")
            raise

    def scan_layers(self) -> List[LayerInfo]:
        """
        Scan all layers in the PSD and extract information.

        Returns:
            List of LayerInfo objects containing layer data and parsed PCS tags
        """
        if not self.psd:
            raise ValueError("PSD file not loaded")

        layers = []
        self._scan_layer_recursive(self.psd, [], layers)

        logger.info(f"Scanned {len(layers)} layers from PSD")
        return layers

    def _scan_layer_recursive(
        self, layer_or_group: Any, path: List[str], result: List[LayerInfo]
    ) -> None:
        """
        Recursively scan layers and groups.

        Args:
            layer_or_group: PSD layer or group
            path: Current path from root
            result: List to append results to
        """
        if hasattr(layer_or_group, "__iter__"):
            # This is the root PSD or a group with layers
            try:
                for i, layer in enumerate(layer_or_group):
                    self._process_single_layer(layer, path, i, result)
            except (TypeError, AttributeError):
                # Handle case where layer_or_group is not iterable
                pass
        else:
            # This is a single layer
            self._process_single_layer(layer_or_group, path, 0, result)

    def _process_single_layer(
        self, layer: Layer, path: List[str], index: int, result: List[LayerInfo]
    ) -> None:
        """
        Process a single layer or group.

        Args:
            layer: The PSD layer
            path: Current path from root
            index: Layer index
            result: List to append results to
        """
        # Skip guide layers (names starting with # or _guide)
        if layer.name.startswith("#") or layer.name.startswith("_guide"):
            logger.debug(f"Skipping guide layer: {layer.name}")
            return

        # Get layer bounding box
        bbox = self._get_layer_bbox(layer)

        # Create layer info
        layer_info = LayerInfo(
            name=layer.name,
            index=index,
            path=path + [layer.name],
            visible=layer.visible,
            bbox=bbox,
            blend_mode=getattr(layer, "blend_mode", "normal"),
        )

        result.append(layer_info)
        logger.debug(
            f"Processed layer: {layer.name} with PCS tag: {layer_info.pcs_tag}"
        )

        # If this is a group, recursively scan its contents
        if hasattr(layer, "__iter__"):
            self._scan_layer_recursive(layer, path + [layer.name], result)

    def _get_layer_bbox(self, layer: Layer) -> tuple:
        """
        Get the bounding box of a layer.

        Args:
            layer: The PSD layer

        Returns:
            Tuple of (left, top, right, bottom)
        """
        try:
            bbox = layer.bbox
            return (bbox.x1, bbox.y1, bbox.x2, bbox.y2)
        except (AttributeError, TypeError):
            # Fallback for layers without bbox
            return (0, 0, 0, 0)

    def find_layers_by_group(
        self, layers: List[LayerInfo], group: str
    ) -> List[LayerInfo]:
        """
        Find all layers belonging to a specific PCS group.

        Args:
            layers: List of LayerInfo objects
            group: Group name to filter by

        Returns:
            List of layers in the specified group
        """
        return [
            layer
            for layer in layers
            if layer.pcs_tag
            and layer.pcs_tag.group
            and layer.pcs_tag.group.lower() == group.lower()
        ]

    def find_layers_by_part(
        self, layers: List[LayerInfo], part: str
    ) -> List[LayerInfo]:
        """
        Find all layers belonging to a specific PCS part.

        Args:
            layers: List of LayerInfo objects
            part: Part name to filter by

        Returns:
            List of layers for the specified part
        """
        return [
            layer
            for layer in layers
            if layer.pcs_tag
            and layer.pcs_tag.part
            and layer.pcs_tag.part.lower() == part.lower()
        ]

    def get_layer_statistics(self, layers: List[LayerInfo]) -> Dict[str, Any]:
        """
        Generate statistics about the scanned layers.

        Args:
            layers: List of LayerInfo objects

        Returns:
            Dictionary containing layer statistics
        """
        stats = {
            "total_layers": len(layers),
            "tagged_layers": 0,
            "groups": {},
            "parts": {},
            "visemes": set(),
            "states": set(),
            "emotions": set(),
        }

        for layer in layers:
            if layer.pcs_tag:
                stats["tagged_layers"] += 1

                if layer.pcs_tag.group:
                    group = layer.pcs_tag.group
                    stats["groups"][group] = stats["groups"].get(group, 0) + 1

                if layer.pcs_tag.part:
                    part = layer.pcs_tag.part
                    stats["parts"][part] = stats["parts"].get(part, 0) + 1

                if layer.pcs_tag.viseme:
                    stats["visemes"].add(layer.pcs_tag.viseme)

                if layer.pcs_tag.state:
                    stats["states"].add(layer.pcs_tag.state)

                if layer.pcs_tag.emotion:
                    stats["emotions"].add(layer.pcs_tag.emotion)

        # Convert sets to lists for JSON serialization
        stats["visemes"] = sorted(list(stats["visemes"]))
        stats["states"] = sorted(list(stats["states"]))
        stats["emotions"] = sorted(list(stats["emotions"]))

        return stats
