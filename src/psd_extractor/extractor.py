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

        # Check which expressions can be mapped
        mappable_states = {}
        for state, expr_names in self.expression_mapping.items():
            found_expressions = [
                name for name in expr_names if name in available_expressions
            ]
            if found_expressions:
                mappable_states[state] = found_expressions

        return {
            "psd_info": basic_info,
            "available_expressions": available_expressions,
            "mappable_lip_sync_states": mappable_states,
            "total_extractable": len(mappable_states),
            "expression_mapping": self.expression_mapping,
        }
