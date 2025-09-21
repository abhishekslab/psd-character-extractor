"""
Character Expression Extractor

Extracts character expressions from PSD files and maps them to lip sync states.
"""

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Union

from psd_tools import PSDImage

from .analyzer import PSDAnalyzer
from .optimizer import ImageOptimizer

logger = logging.getLogger(__name__)


class CharacterExtractor:
    """Main class for extracting character expressions from PSD files."""

    # Default expression mapping for lip sync
    DEFAULT_EXPRESSION_MAPPING = {
        "closed": ["normal", "neutral", "smug"],
        "small": ["smile", "smile 2", "happy"],
        "medium": ["delighted", "annoyed", "excited"],
        "wide": ["shocked", "laugh", "surprised"],
    }

    def __init__(
        self, psd_path: str, expression_mapping: Optional[Dict[str, List[str]]] = None
    ):
        """
        Initialize the character extractor.

        Args:
            psd_path: Path to the PSD file
            expression_mapping: Custom mapping of lip sync states to expression names
        """
        self.psd_path = psd_path
        self.psd = None
        self.analyzer = PSDAnalyzer(psd_path)
        self.optimizer = ImageOptimizer()

        self.expression_mapping = expression_mapping or self.DEFAULT_EXPRESSION_MAPPING
        self._load_psd()

    def _load_psd(self) -> None:
        """Load and validate the PSD file."""
        try:
            self.psd = PSDImage.open(self.psd_path)
            logger.info(f"Loaded PSD file: {self.psd_path}")
        except Exception as e:
            logger.error(f"Failed to load PSD file: {e}")
            raise

    def set_expression_mapping(self, mapping: Dict[str, List[str]]) -> None:
        """
        Set custom expression mapping for lip sync states.

        Args:
            mapping: Dictionary mapping lip sync states to expression layer names
        """
        self.expression_mapping = mapping
        logger.info(f"Updated expression mapping: {list(mapping.keys())}")

    def get_available_expressions(self) -> List[str]:
        """
        Get list of all available expression layer names.

        Returns:
            List of expression layer names found in the PSD
        """
        expressions = self.analyzer.find_expression_layers()
        return [expr["name"] for expr in expressions]

    def get_all_components(self) -> Dict[str, List[Dict[str, any]]]:
        """
        Get all character components organized by category.

        Returns:
            Dictionary mapping component categories to lists of component details
        """
        return self.analyzer.find_all_components()

    def get_extractable_components(self) -> List[Dict[str, any]]:
        """
        Get all components that can be individually extracted.

        Returns:
            List of extractable component details
        """
        return self.analyzer.get_extractable_components()

    def get_components_by_category(self, category: str) -> List[Dict[str, any]]:
        """
        Get all components in a specific category.

        Args:
            category: Component category to filter by

        Returns:
            List of components in the specified category
        """
        return self.analyzer.get_components_by_category(category)

    def get_raw_layers(self) -> List[Dict[str, any]]:
        """
        Get all PSD layers as raw list without classification.

        Returns:
            List of raw layer information
        """
        return self.analyzer.get_raw_layers()

    def extract_raw_layer(self, layer_name: str) -> Optional[any]:
        """
        Extract a single layer in complete isolation (no other layers visible).

        Args:
            layer_name: Name of the layer to extract

        Returns:
            PIL Image of the isolated layer, or None if extraction fails
        """
        if not self.psd:
            raise ValueError("PSD file not loaded")

        try:
            logger.info(f"Starting raw layer extraction for: '{layer_name}'")

            # Find the target layer
            target_layer = self.analyzer.get_layer_by_name(layer_name)
            if not target_layer:
                logger.error(f"Layer '{layer_name}' not found in PSD")
                return None

            logger.debug(
                f"Found target layer: '{target_layer.name}' (type: {type(target_layer)})"
            )

            # Save original visibility states
            original_visibility = {}
            all_layers = list(self.psd.descendants())
            logger.debug(f"Found {len(all_layers)} total layers in PSD")

            visible_layers_before = []
            for layer in all_layers:
                if hasattr(layer, "visible"):
                    original_visibility[layer.name] = layer.visible
                    if layer.visible:
                        visible_layers_before.append(layer.name)

            logger.debug(f"Originally visible layers: {visible_layers_before}")

            try:
                # Hide ALL layers first
                hidden_count = 0
                for layer in all_layers:
                    if hasattr(layer, "visible"):
                        layer.visible = False
                        hidden_count += 1

                logger.debug(f"Hidden {hidden_count} layers")

                # Show ONLY the target layer - no context, no base layers
                target_layer.visible = True

                # CRITICAL: Also make sure all parent groups are visible
                # If a parent group is hidden, the child layer won't show
                current = target_layer
                parent_groups_made_visible = []
                while hasattr(current, "parent") and current.parent is not None:
                    parent = current.parent
                    if hasattr(parent, "visible") and hasattr(parent, "name"):
                        if not parent.visible:
                            parent.visible = True
                            parent_groups_made_visible.append(parent.name)
                            logger.debug(f"Made parent group visible: {parent.name}")
                    current = parent

                logger.info(
                    f"Isolated layer '{layer_name}' - made {len(parent_groups_made_visible)} parent groups visible: {parent_groups_made_visible}"
                )

                # Debug: Check final visibility state
                visible_after = []
                for layer in all_layers:
                    if (
                        hasattr(layer, "visible")
                        and layer.visible
                        and hasattr(layer, "name")
                    ):
                        visible_after.append(layer.name)

                logger.debug(f"Layers visible after isolation: {visible_after}")

                # Try two different approaches for layer extraction

                # Approach 1: Direct layer compositing (try this first for better isolation)
                try:
                    if hasattr(target_layer, "composite") and callable(
                        target_layer.composite
                    ):
                        logger.debug(
                            f"Attempting direct layer composite for: {layer_name}"
                        )
                        layer_image = target_layer.composite()

                        if layer_image and layer_image.size != (0, 0):
                            logger.info(
                                f"Direct layer composite successful - Size: {layer_image.size}"
                            )

                            # Check if this gives us better isolation
                            if hasattr(layer_image, "getextrema"):
                                try:
                                    rgba_image = layer_image.convert("RGBA")
                                    alpha_extrema = rgba_image.split()[-1].getextrema()
                                    logger.debug(
                                        f"Direct layer alpha range: {alpha_extrema}"
                                    )

                                    if alpha_extrema[0] == 0:  # Has transparency
                                        logger.info(
                                            f"Direct layer extraction has transparency - using this method"
                                        )
                                        return layer_image
                                except Exception as e:
                                    logger.debug(
                                        f"Could not analyze direct layer transparency: {e}"
                                    )

                            return layer_image
                        else:
                            logger.debug(
                                f"Direct layer composite returned empty/invalid image"
                            )
                    else:
                        logger.debug(
                            f"Layer {layer_name} does not support direct composite"
                        )
                except Exception as e:
                    logger.debug(f"Direct layer composite failed: {e}")

                # Approach 2: Full PSD composite with visibility manipulation (fallback)
                logger.debug(
                    f"Falling back to full PSD composite with visibility manipulation"
                )
                composite_image = self.psd.composite()

                if composite_image:
                    logger.info(
                        f"PSD composite extraction: {layer_name} - Size: {composite_image.size}"
                    )

                    # Additional debug: Check if image is actually different from full composite
                    if hasattr(composite_image, "getextrema"):
                        try:
                            # Convert to RGBA to check alpha channel
                            rgba_image = composite_image.convert("RGBA")
                            alpha_extrema = rgba_image.split()[
                                -1
                            ].getextrema()  # Get alpha channel extrema
                            logger.debug(f"PSD composite alpha range: {alpha_extrema}")

                            if alpha_extrema[0] == 0:  # Has transparent pixels
                                logger.info(
                                    f"PSD composite has transparency - partial isolation achieved"
                                )
                            else:
                                logger.warning(
                                    f"PSD composite has no transparency - likely full composite"
                                )
                        except Exception as e:
                            logger.debug(
                                f"Could not analyze PSD composite transparency: {e}"
                            )
                else:
                    logger.warning(
                        f"PSD composite returned None for raw layer: {layer_name}"
                    )

                return composite_image

            finally:
                # Restore original visibility states
                restored_count = 0
                for layer in all_layers:
                    if hasattr(layer, "visible") and layer.name in original_visibility:
                        layer.visible = original_visibility[layer.name]
                        restored_count += 1

                logger.debug(f"Restored visibility for {restored_count} layers")

        except Exception as e:
            logger.error(f"Failed to extract raw layer '{layer_name}': {e}")
            return None

    def extract_expression(self, expression_name: str) -> Optional[any]:
        """
        Extract a single expression from the PSD.

        Args:
            expression_name: Name of the expression layer to extract

        Returns:
            PIL Image of the extracted expression, or None if extraction fails
        """
        if not self.psd:
            raise ValueError("PSD file not loaded")

        try:
            # Find the Expression group
            expression_group = self.analyzer.get_expression_group()
            if not expression_group:
                logger.error("No expression group found in PSD")
                return None

            # Hide all expression layers first
            if hasattr(expression_group, "_layers"):
                for expr_layer in expression_group._layers:
                    expr_layer.visible = False

            # Find and enable the target expression
            target_expression = self.analyzer.get_layer_by_name(expression_name)
            if not target_expression:
                logger.error(f"Expression '{expression_name}' not found")
                return None

            # Enable the target expression
            original_visibility = target_expression.visible
            target_expression.visible = True

            try:
                # Composite the entire image
                composite_image = self.psd.composite()
                logger.info(f"Successfully extracted expression: {expression_name}")
                return composite_image

            finally:
                # Restore original visibility
                target_expression.visible = original_visibility

        except Exception as e:
            logger.error(f"Failed to extract expression '{expression_name}': {e}")
            return None

    def extract_component(self, component_name: str) -> Optional[any]:
        """
        Extract a single component from the PSD.

        Args:
            component_name: Name of the component layer to extract

        Returns:
            PIL Image of the extracted component, or None if extraction fails
        """
        if not self.psd:
            raise ValueError("PSD file not loaded")

        try:
            # Find the target component
            target_component = self.analyzer.get_layer_by_name(component_name)
            if not target_component:
                logger.error(f"Component '{component_name}' not found")
                return None

            # Save original visibility states
            original_visibility = {}
            all_layers = list(self.psd.descendants())

            for layer in all_layers:
                if hasattr(layer, "visible"):
                    original_visibility[layer.name] = layer.visible

            try:
                # Hide all layers first
                for layer in all_layers:
                    if hasattr(layer, "visible"):
                        layer.visible = False

                # Show only the target component
                target_component.visible = True

                # For component extraction, we might need to show related base layers
                # Show body/base layers if extracting clothing/accessories
                extractable_components = self.get_extractable_components()
                target_category = None

                for comp in extractable_components:
                    if comp["name"] == component_name:
                        target_category = comp["category"]
                        break

                # Show base layers for proper context
                if target_category in ["clothing", "accessories", "shoes", "bottom"]:
                    for layer in all_layers:
                        if hasattr(layer, "visible") and hasattr(layer, "name"):
                            layer_name_lower = layer.name.lower()
                            if any(
                                keyword in layer_name_lower
                                for keyword in ["body", "base", "skin"]
                            ):
                                layer.visible = True

                # Composite the image
                composite_image = self.psd.composite()
                logger.info(f"Successfully extracted component: {component_name}")
                return composite_image

            finally:
                # Restore original visibility states
                for layer in all_layers:
                    if hasattr(layer, "visible") and layer.name in original_visibility:
                        layer.visible = original_visibility[layer.name]

        except Exception as e:
            logger.error(f"Failed to extract component '{component_name}': {e}")
            return None

    def extract_expressions(
        self,
        custom_mapping: Optional[Dict[str, List[str]]] = None,
        target_states: Optional[List[str]] = None,
    ) -> Dict[str, any]:
        """
        Extract multiple expressions mapped to lip sync states.

        Args:
            custom_mapping: Optional custom expression mapping
            target_states: Optional list of specific states to extract

        Returns:
            Dictionary mapping lip sync states to PIL Images
        """
        mapping = custom_mapping or self.expression_mapping
        states_to_extract = target_states or list(mapping.keys())

        extracted_expressions = {}

        for sync_state in states_to_extract:
            if sync_state not in mapping:
                logger.warning(f"Sync state '{sync_state}' not found in mapping")
                continue

            expression_names = mapping[sync_state]
            logger.info(f"Extracting for lip sync state: {sync_state}")

            # Try each expression in the mapping until one succeeds
            extracted = False
            for expression_name in expression_names:
                image = self.extract_expression(expression_name)
                if image is not None:
                    extracted_expressions[sync_state] = image
                    logger.info(f"  ✓ Used '{expression_name}' for {sync_state} state")
                    extracted = True
                    break
                else:
                    logger.warning(f"  ✗ Failed to extract '{expression_name}'")

            if not extracted:
                logger.warning(
                    f"  ⚠ No suitable expression found for {sync_state} state"
                )

        logger.info(
            f"Successfully extracted {len(extracted_expressions)}/{len(states_to_extract)} expressions"
        )
        return extracted_expressions

    def extract_all_expressions(self) -> Dict[str, any]:
        """
        Extract all available expressions from the PSD.

        Returns:
            Dictionary mapping expression names to PIL Images
        """
        available_expressions = self.get_available_expressions()
        extracted = {}

        for expr_name in available_expressions:
            image = self.extract_expression(expr_name)
            if image is not None:
                extracted[expr_name] = image

        logger.info(
            f"Extracted {len(extracted)}/{len(available_expressions)} available expressions"
        )
        return extracted

    def extract_components_by_category(self, category: str) -> Dict[str, any]:
        """
        Extract all components in a specific category.

        Args:
            category: Component category to extract

        Returns:
            Dictionary mapping component names to PIL Images
        """
        components = self.get_components_by_category(category)
        extracted = {}

        for component in components:
            if component["type"] == "LAYER":  # Only extract individual layers
                component_name = component["name"]
                image = self.extract_component(component_name)
                if image is not None:
                    extracted[component_name] = image

        logger.info(
            f"Extracted {len(extracted)}/{len(components)} components from category '{category}'"
        )
        return extracted

    def extract_all_components(self) -> Dict[str, Dict[str, any]]:
        """
        Extract all available components organized by category.

        Returns:
            Dictionary mapping categories to dictionaries of component names and PIL Images
        """
        all_components = self.get_all_components()
        extracted_by_category = {}

        for category, components in all_components.items():
            category_extracted = {}

            for component in components:
                if component["type"] == "LAYER":  # Only extract individual layers
                    component_name = component["name"]
                    image = self.extract_component(component_name)
                    if image is not None:
                        category_extracted[component_name] = image

            if (
                category_extracted
            ):  # Only include categories with successful extractions
                extracted_by_category[category] = category_extracted

        total_extracted = sum(
            len(category_dict) for category_dict in extracted_by_category.values()
        )
        logger.info(
            f"Extracted {total_extracted} components across {len(extracted_by_category)} categories"
        )
        return extracted_by_category

    def save_expressions(
        self,
        expressions: Dict[str, any],
        output_dir: str,
        optimize: bool = True,
        prefix: str = "character",
    ) -> Dict[str, str]:
        """
        Save extracted expressions to files.

        Args:
            expressions: Dictionary of expressions (from extract_expressions)
            output_dir: Directory to save images
            optimize: Whether to optimize images for web
            prefix: Prefix for output filenames

        Returns:
            Dictionary mapping expression names to saved file paths
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        saved_files = {}

        for expr_name, image in expressions.items():
            if image is None:
                continue

            filename = f"{prefix}-{expr_name}.png"
            file_path = output_path / filename

            if optimize:
                # Apply optimization before saving
                image = self.optimizer.optimize_for_web(image)

            try:
                image.save(str(file_path), "PNG")
                saved_files[expr_name] = str(file_path)
                logger.info(f"Saved: {file_path}")

            except Exception as e:
                logger.error(f"Failed to save {expr_name}: {e}")

        logger.info(f"Saved {len(saved_files)} expression files to {output_dir}")
        return saved_files

    def extract_and_save(
        self,
        output_dir: str,
        custom_mapping: Optional[Dict[str, List[str]]] = None,
        optimize: bool = True,
        prefix: str = "character",
    ) -> Dict[str, str]:
        """
        Extract expressions and save them in one step.

        Args:
            output_dir: Directory to save images
            custom_mapping: Optional custom expression mapping
            optimize: Whether to optimize images for web
            prefix: Prefix for output filenames

        Returns:
            Dictionary mapping expression names to saved file paths
        """
        expressions = self.extract_expressions(custom_mapping)
        return self.save_expressions(expressions, output_dir, optimize, prefix)

    def get_extraction_summary(self) -> Dict[str, any]:
        """
        Get a summary of what can be extracted from this PSD.

        Returns:
            Dictionary containing extraction possibilities
        """
        basic_info = self.analyzer.get_basic_info()
        available_expressions = self.get_available_expressions()
        all_components = self.get_all_components()
        extractable_components = self.get_extractable_components()

        # Check which expressions can be mapped
        mappable_states = {}
        for state, expr_names in self.expression_mapping.items():
            found_expressions = [
                name for name in expr_names if name in available_expressions
            ]
            if found_expressions:
                mappable_states[state] = found_expressions

        # Component statistics
        component_stats = {}
        for category, components in all_components.items():
            extractable_count = len([c for c in components if c["type"] == "LAYER"])
            if extractable_count > 0:
                component_stats[category] = {
                    "total": len(components),
                    "extractable": extractable_count,
                    "components": [
                        c["name"] for c in components if c["type"] == "LAYER"
                    ],
                }

        return {
            "psd_info": basic_info,
            "available_expressions": available_expressions,
            "mappable_lip_sync_states": mappable_states,
            "total_extractable_expressions": len(mappable_states),
            "expression_mapping": self.expression_mapping,
            "all_components": all_components,
            "component_statistics": component_stats,
            "total_extractable_components": len(extractable_components),
            "extractable_components": [
                {
                    "name": comp["name"],
                    "category": comp["category"],
                    "dimensions": comp["dimensions"],
                }
                for comp in extractable_components
            ],
        }
