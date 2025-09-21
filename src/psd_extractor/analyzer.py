"""
PSD Structure Analyzer

Analyzes Photoshop PSD files to understand layer organization
and identify potential character expressions.
"""

import logging
from typing import Dict, List, Optional, Tuple

from psd_tools import PSDImage

logger = logging.getLogger(__name__)


class PSDAnalyzer:
    """Analyzes PSD file structure and identifies expression layers."""

    def __init__(self, psd_path: str):
        """
        Initialize analyzer with PSD file.

        Args:
            psd_path: Path to the PSD file to analyze
        """
        self.psd_path = psd_path
        self.psd = None
        self._load_psd()

    def _load_psd(self) -> None:
        """Load PSD file and validate it."""
        try:
            self.psd = PSDImage.open(self.psd_path)
            logger.info(f"Loaded PSD: {self.psd_path}")
        except Exception as e:
            logger.error(f"Failed to load PSD file {self.psd_path}: {e}")
            raise

    def get_basic_info(self) -> Dict[str, any]:
        """
        Get basic information about the PSD file.

        Returns:
            Dictionary containing PSD dimensions, color mode, and layer count
        """
        if not self.psd:
            raise ValueError("PSD file not loaded")

        return {
            "width": self.psd.width,
            "height": self.psd.height,
            "color_mode": self.psd.color_mode,
            "total_layers": len(list(self.psd.descendants())),
            "file_path": self.psd_path,
        }

    def analyze_layer_structure(self) -> Dict[str, any]:
        """
        Analyze the complete layer structure of the PSD.

        Returns:
            Dictionary containing layer tree and analysis results
        """
        if not self.psd:
            raise ValueError("PSD file not loaded")

        layer_tree = []
        for layer in self.psd:
            layer_info = self._analyze_layer(layer)
            layer_tree.append(layer_info)

        return {
            "basic_info": self.get_basic_info(),
            "layer_tree": layer_tree,
            "expression_analysis": self.find_expression_layers(),
            "layer_groups": self._find_layer_groups(),
        }

    def _analyze_layer(self, layer, depth: int = 0) -> Dict[str, any]:
        """
        Recursively analyze a layer and its children.

        Args:
            layer: PSD layer to analyze
            depth: Nesting depth for hierarchy display

        Returns:
            Dictionary containing layer information
        """
        layer_type = "GROUP" if hasattr(layer, "_layers") and layer._layers else "LAYER"

        layer_info = {
            "name": layer.name,
            "type": layer_type,
            "visible": layer.visible,
            "depth": depth,
            "children": [],
        }

        # Add dimension info for regular layers
        if layer_type == "LAYER" and hasattr(layer, "bbox"):
            try:
                bbox = layer.bbox
                if bbox:
                    width = bbox[2] - bbox[0]
                    height = bbox[3] - bbox[1]
                    layer_info.update(
                        {"width": width, "height": height, "x": bbox[0], "y": bbox[1]}
                    )
            except Exception:
                pass

        # Recursively process child layers
        if hasattr(layer, "_layers") and layer._layers:
            for child in layer._layers:
                child_info = self._analyze_layer(child, depth + 1)
                layer_info["children"].append(child_info)

        return layer_info

    def find_expression_layers(self) -> List[Dict[str, any]]:
        """
        Find layers that likely contain facial expressions.

        Returns:
            List of dictionaries containing potential expression layers
        """
        if not self.psd:
            raise ValueError("PSD file not loaded")

        expression_keywords = [
            "mouth",
            "expression",
            "face",
            "emotion",
            "smile",
            "happy",
            "sad",
            "angry",
            "neutral",
            "open",
            "closed",
            "surprised",
            "shocked",
            "delighted",
            "smug",
            "annoyed",
            "sleepy",
            "laugh",
        ]

        potential_expressions = []
        all_layers = list(self.psd.descendants())

        for layer in all_layers:
            layer_name_lower = layer.name.lower()

            # Check if layer name contains expression keywords
            matched_keywords = [
                kw for kw in expression_keywords if kw in layer_name_lower
            ]

            if matched_keywords:
                layer_info = {
                    "name": layer.name,
                    "keywords": matched_keywords,
                    "visible": layer.visible,
                    "layer_object": layer,
                }

                # Add dimension info if available
                if hasattr(layer, "bbox"):
                    try:
                        bbox = layer.bbox
                        if bbox:
                            layer_info.update(
                                {
                                    "width": bbox[2] - bbox[0],
                                    "height": bbox[3] - bbox[1],
                                    "x": bbox[0],
                                    "y": bbox[1],
                                }
                            )
                    except Exception:
                        pass

                potential_expressions.append(layer_info)

        return potential_expressions

    def _find_layer_groups(self) -> Dict[str, List[str]]:
        """
        Find and categorize layer groups (hair, costume, accessories, etc.).

        Returns:
            Dictionary mapping group types to layer names
        """
        if not self.psd:
            raise ValueError("PSD file not loaded")

        group_keywords = {
            "hair": ["hair", "hairstyle", "wig"],
            "costume": ["costume", "outfit", "clothes", "dress", "uniform"],
            "accessories": ["accessories", "glasses", "hat", "jewelry"],
            "expression": ["expression", "face", "emotion"],
            "body": ["body", "base", "skin"],
            "background": ["background", "bg", "backdrop"],
        }

        layer_groups = {group: [] for group in group_keywords.keys()}
        all_layers = list(self.psd.descendants())

        for layer in all_layers:
            layer_name_lower = layer.name.lower()

            for group_type, keywords in group_keywords.items():
                if any(keyword in layer_name_lower for keyword in keywords):
                    layer_groups[group_type].append(layer.name)
                    break

        return layer_groups

    def get_layer_by_name(self, layer_name: str):
        """
        Find a layer by its exact name.

        Args:
            layer_name: Exact name of the layer to find

        Returns:
            Layer object if found, None otherwise
        """
        if not self.psd:
            raise ValueError("PSD file not loaded")

        for layer in self.psd.descendants():
            if layer.name == layer_name:
                return layer
        return None

    def get_expression_group(self) -> Optional[any]:
        """
        Find the main expression group layer.

        Returns:
            Expression group layer if found, None otherwise
        """
        expression_group_names = ["Expression", "Expressions", "Face", "Emotions"]

        for name in expression_group_names:
            group = self.get_layer_by_name(name)
            if group and hasattr(group, "_layers"):
                return group

        return None

    def list_all_layers(self) -> List[str]:
        """
        Get a simple list of all layer names in the PSD.

        Returns:
            List of all layer names
        """
        if not self.psd:
            raise ValueError("PSD file not loaded")

        return [layer.name for layer in self.psd.descendants() if layer.name.strip()]

    def print_analysis_report(self) -> None:
        """Print a comprehensive analysis report to console."""
        analysis = self.analyze_layer_structure()

        print(f"PSD Analysis Report: {self.psd_path}")
        print("=" * 50)

        # Basic info
        info = analysis["basic_info"]
        print(f"Dimensions: {info['width']} x {info['height']}")
        print(f"Color Mode: {info['color_mode']}")
        print(f"Total Layers: {info['total_layers']}")

        # Expression layers
        expressions = analysis["expression_analysis"]
        print(f"\nPotential Expression Layers ({len(expressions)}):")
        for expr in expressions:
            print(f"  - {expr['name']} (keywords: {', '.join(expr['keywords'])})")

        # Layer groups
        groups = analysis["layer_groups"]
        print("\nLayer Groups:")
        for group_type, layers in groups.items():
            if layers:
                print(f"  {group_type.title()}: {len(layers)} layers")

        print("\n" + "=" * 50)
