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
            "component_analysis": self.find_all_components(),
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

    def find_all_components(self) -> Dict[str, List[Dict[str, any]]]:
        """
        Find and categorize all character components with detailed information.

        Returns:
            Dictionary mapping component types to lists of component details
        """
        if not self.psd:
            raise ValueError("PSD file not loaded")

        component_keywords = {
            "hair": ["hair", "hairstyle", "wig", "bangs", "ponytail", "braid", "pigtail"],
            "clothing": ["costume", "outfit", "clothes", "dress", "uniform", "shirt", "top", "jacket", "coat", "vest", "sweater"],
            "bottom": ["pants", "skirt", "shorts", "trousers", "jeans", "leggings"],
            "shoes": ["shoes", "boots", "sandals", "sneakers", "heels", "footwear"],
            "accessories": ["accessories", "glasses", "hat", "cap", "crown", "jewelry", "necklace", "earrings", "bracelet", "ring", "bow", "ribbon"],
            "expression": ["expression", "face", "emotion", "mouth", "smile", "happy", "sad", "angry", "neutral", "surprised", "shocked", "delighted", "smug", "annoyed", "sleepy", "laugh"],
            "eyes": ["eyes", "eye", "wink", "blink", "eyelash", "eyebrow"],
            "body": ["body", "base", "skin", "torso", "chest", "bust", "arms", "legs", "hands"],
            "weapons": ["weapon", "sword", "gun", "staff", "wand", "shield", "bow", "knife"],
            "effects": ["effect", "glow", "sparkle", "shadow", "highlight", "aura", "magic"],
            "background": ["background", "bg", "backdrop", "scenery", "environment"],
            "other": []  # Will contain uncategorized layers
        }

        components = {category: [] for category in component_keywords.keys()}
        all_layers = list(self.psd.descendants())
        categorized_layers = set()

        for layer in all_layers:
            if not layer.name or not layer.name.strip():
                continue

            layer_name_lower = layer.name.lower()
            categorized = False

            # Try to categorize based on keywords
            for category, keywords in component_keywords.items():
                if category == "other":
                    continue

                if any(keyword in layer_name_lower for keyword in keywords):
                    component_info = self._get_component_info(layer)
                    components[category].append(component_info)
                    categorized_layers.add(layer.name)
                    categorized = True
                    break

            # Add uncategorized layers to "other"
            if not categorized:
                component_info = self._get_component_info(layer)
                components["other"].append(component_info)

        return components

    def _get_component_info(self, layer) -> Dict[str, any]:
        """
        Extract detailed information about a layer component.

        Args:
            layer: PSD layer object

        Returns:
            Dictionary containing component details
        """
        component_info = {
            "name": layer.name,
            "visible": layer.visible,
            "layer_object": layer,
            "type": "GROUP" if hasattr(layer, "_layers") and layer._layers else "LAYER",
        }

        # Add dimension info if available
        if hasattr(layer, "bbox") and component_info["type"] == "LAYER":
            try:
                bbox = layer.bbox
                if bbox:
                    component_info.update({
                        "width": bbox[2] - bbox[0],
                        "height": bbox[3] - bbox[1],
                        "x": bbox[0],
                        "y": bbox[1],
                    })
            except Exception:
                pass

        # Add children count for groups
        if component_info["type"] == "GROUP":
            try:
                children_count = len(list(layer)) if hasattr(layer, "__iter__") else 0
                component_info["children_count"] = children_count
            except Exception:
                component_info["children_count"] = 0

        return component_info

    def _find_layer_groups(self) -> Dict[str, List[str]]:
        """
        Find and categorize layer groups (hair, costume, accessories, etc.).

        Note: This method is kept for backward compatibility.
        Use find_all_components() for more detailed component information.

        Returns:
            Dictionary mapping group types to layer names
        """
        components = self.find_all_components()

        # Convert detailed components back to simple name lists for compatibility
        layer_groups = {}
        for category, component_list in components.items():
            layer_groups[category] = [comp["name"] for comp in component_list]

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

    def get_extractable_components(self) -> List[Dict[str, any]]:
        """
        Get all components that can be individually extracted.

        Returns:
            List of component dictionaries with extraction metadata
        """
        if not self.psd:
            raise ValueError("PSD file not loaded")

        extractable = []
        all_components = self.find_all_components()

        for category, components in all_components.items():
            for component in components:
                # Only include layers that are not groups and have meaningful content
                if component["type"] == "LAYER" and component.get("width", 0) > 0 and component.get("height", 0) > 0:
                    extractable_info = {
                        "name": component["name"],
                        "category": category,
                        "visible": component["visible"],
                        "dimensions": {
                            "width": component.get("width", 0),
                            "height": component.get("height", 0),
                            "x": component.get("x", 0),
                            "y": component.get("y", 0),
                        },
                        "layer_object": component["layer_object"],
                    }
                    extractable.append(extractable_info)

        return extractable

    def get_components_by_category(self, category: str) -> List[Dict[str, any]]:
        """
        Get all components in a specific category.

        Args:
            category: Component category to filter by

        Returns:
            List of components in the specified category
        """
        all_components = self.find_all_components()
        return all_components.get(category, [])

    def get_raw_layers(self) -> List[Dict[str, any]]:
        """
        Get all PSD layers as raw list without any classification or grouping.

        Returns:
            List of layer dictionaries with basic info only
        """
        if not self.psd:
            raise ValueError("PSD file not loaded")

        raw_layers = []
        all_layers = list(self.psd.descendants())

        for layer in all_layers:
            if not layer.name or not layer.name.strip():
                continue

            layer_info = {
                "name": layer.name,
                "visible": layer.visible,
                "type": "GROUP" if hasattr(layer, "_layers") and layer._layers else "LAYER",
            }

            # Add dimension info if available and it's a layer
            if layer_info["type"] == "LAYER" and hasattr(layer, "bbox"):
                try:
                    bbox = layer.bbox
                    if bbox:
                        layer_info.update({
                            "width": bbox[2] - bbox[0],
                            "height": bbox[3] - bbox[1],
                            "x": bbox[0],
                            "y": bbox[1],
                        })
                except Exception:
                    pass

            raw_layers.append(layer_info)

        return raw_layers

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
