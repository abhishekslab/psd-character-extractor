"""
Async wrapper for PSD Character Extractor

Provides async interfaces for the main extractor classes to support
web application non-blocking operations.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union
from concurrent.futures import ThreadPoolExecutor

from ..analyzer import PSDAnalyzer
from ..extractor import CharacterExtractor

logger = logging.getLogger(__name__)


class AsyncPSDExtractor:
    """Async wrapper for PSD Character Extractor operations."""

    def __init__(self, max_workers: int = 2):
        """
        Initialize the async extractor.

        Args:
            max_workers: Maximum number of worker threads for CPU-bound operations
        """
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    async def analyze_psd(self, psd_path: str) -> Dict:
        """
        Analyze PSD file structure asynchronously.

        Args:
            psd_path: Path to the PSD file

        Returns:
            Dictionary containing analysis results
        """
        loop = asyncio.get_event_loop()

        def _analyze():
            try:
                analyzer = PSDAnalyzer(psd_path)
                return analyzer.analyze_layer_structure()
            except Exception as e:
                logger.error(f"Failed to analyze PSD {psd_path}: {e}")
                raise

        return await loop.run_in_executor(self.executor, _analyze)

    async def get_available_expressions(self, psd_path: str) -> List[str]:
        """
        Get available expressions from PSD file asynchronously.

        Args:
            psd_path: Path to the PSD file

        Returns:
            List of expression layer names
        """
        loop = asyncio.get_event_loop()

        def _get_expressions():
            try:
                extractor = CharacterExtractor(psd_path)
                return extractor.get_available_expressions()
            except Exception as e:
                logger.error(f"Failed to get expressions from {psd_path}: {e}")
                raise

        return await loop.run_in_executor(self.executor, _get_expressions)

    async def get_all_components(self, psd_path: str) -> Dict[str, List[Dict[str, any]]]:
        """
        Get all character components from PSD file asynchronously.

        Args:
            psd_path: Path to the PSD file

        Returns:
            Dictionary mapping component categories to lists of component details
        """
        loop = asyncio.get_event_loop()

        def _get_components():
            try:
                extractor = CharacterExtractor(psd_path)
                return extractor.get_all_components()
            except Exception as e:
                logger.error(f"Failed to get components from {psd_path}: {e}")
                raise

        return await loop.run_in_executor(self.executor, _get_components)

    async def get_extractable_components(self, psd_path: str) -> List[Dict[str, any]]:
        """
        Get extractable components from PSD file asynchronously.

        Args:
            psd_path: Path to the PSD file

        Returns:
            List of extractable component details
        """
        loop = asyncio.get_event_loop()

        def _get_extractable():
            try:
                extractor = CharacterExtractor(psd_path)
                return extractor.get_extractable_components()
            except Exception as e:
                logger.error(f"Failed to get extractable components from {psd_path}: {e}")
                raise

        return await loop.run_in_executor(self.executor, _get_extractable)

    async def extract_expressions(
        self,
        psd_path: str,
        expression_mapping: Dict[str, List[str]],
        output_dir: str
    ) -> Dict[str, Dict]:
        """
        Extract expressions with mapping asynchronously.

        Args:
            psd_path: Path to the PSD file
            expression_mapping: Mapping of lip sync states to expression names
            output_dir: Output directory for extracted images

        Returns:
            Dictionary containing extraction results with file paths
        """
        loop = asyncio.get_event_loop()

        def _extract():
            try:
                extractor = CharacterExtractor(psd_path, expression_mapping)
                output_path = Path(output_dir)
                output_path.mkdir(parents=True, exist_ok=True)

                results = {}

                # Extract expressions for each lip sync state
                for state, expressions in expression_mapping.items():
                    state_results = []

                    for expr_name in expressions:
                        try:
                            # Extract the expression
                            image = extractor.extract_expression(expr_name)

                            if image:
                                # Save the image
                                safe_name = expr_name.replace(" ", "_").lower()
                                filename = f"{state}_{safe_name}.png"
                                filepath = output_path / filename

                                # Optimize for web if needed
                                optimized = extractor.optimizer.optimize_for_web(image)
                                optimized.save(filepath, "PNG")

                                state_results.append({
                                    "name": expr_name,
                                    "filename": filename,
                                    "filepath": str(filepath),
                                    "size": image.size
                                })

                                logger.info(f"Extracted {expr_name} -> {filename}")
                            else:
                                logger.warning(f"Failed to extract expression: {expr_name}")

                        except Exception as e:
                            logger.error(f"Error extracting {expr_name}: {e}")

                    results[state] = state_results

                return results

            except Exception as e:
                logger.error(f"Failed to extract expressions from {psd_path}: {e}")
                raise

        return await loop.run_in_executor(self.executor, _extract)

    async def extract_components(
        self,
        psd_path: str,
        component_mapping: Dict[str, List[str]],
        output_dir: str
    ) -> Dict[str, Dict]:
        """
        Extract individual components asynchronously.

        Args:
            psd_path: Path to the PSD file
            component_mapping: Mapping of categories to component names
            output_dir: Output directory for extracted images

        Returns:
            Dictionary containing extraction results with file paths
        """
        loop = asyncio.get_event_loop()

        def _extract_components():
            try:
                extractor = CharacterExtractor(psd_path)
                output_path = Path(output_dir)
                output_path.mkdir(parents=True, exist_ok=True)

                results = {}

                # Extract components for each category
                for category, component_names in component_mapping.items():
                    category_results = []

                    for comp_name in component_names:
                        try:
                            # Extract the component
                            image = extractor.extract_component(comp_name)

                            if image:
                                # Save the image
                                safe_name = comp_name.replace(" ", "_").lower()
                                filename = f"{category}_{safe_name}.png"
                                filepath = output_path / filename

                                # Optimize for web if needed
                                optimized = extractor.optimizer.optimize_for_web(image)
                                optimized.save(filepath, "PNG")

                                category_results.append({
                                    "name": comp_name,
                                    "filename": filename,
                                    "filepath": str(filepath),
                                    "size": image.size
                                })

                                logger.info(f"Extracted {comp_name} -> {filename}")
                            else:
                                logger.warning(f"Failed to extract component: {comp_name}")

                        except Exception as e:
                            logger.error(f"Error extracting component {comp_name}: {e}")

                    results[category] = category_results

                return results

            except Exception as e:
                logger.error(f"Failed to extract components from {psd_path}: {e}")
                raise

        return await loop.run_in_executor(self.executor, _extract_components)

    async def create_mapping_suggestions(self, psd_path: str) -> Dict[str, List[str]]:
        """
        Create automatic mapping suggestions based on layer names.
        Now supports both expression mapping and component organization.

        Args:
            psd_path: Path to the PSD file

        Returns:
            Dictionary with suggested mappings for expressions
        """
        loop = asyncio.get_event_loop()

        def _suggest_mapping():
            try:
                analyzer = PSDAnalyzer(psd_path)
                expressions = analyzer.find_expression_layers()

                # Use default mapping as base for expressions (for backward compatibility)
                suggestions = {
                    'closed': [],
                    'small': [],
                    'medium': [],
                    'wide': [],
                    'unmapped': []
                }

                # Keywords for automatic classification
                mapping_keywords = {
                    'closed': ['normal', 'neutral', 'calm', 'smug', 'sleepy', 'resting'],
                    'small': ['smile', 'happy', 'pleased', 'content'],
                    'medium': ['delighted', 'excited', 'talking', 'annoyed', 'angry', 'sad'],
                    'wide': ['shocked', 'surprised', 'laugh', 'amazed', 'wow']
                }

                for expr in expressions:
                    expr_name = expr['name'].lower()
                    mapped = False

                    # Try to classify based on keywords
                    for state, keywords in mapping_keywords.items():
                        if any(keyword in expr_name for keyword in keywords):
                            suggestions[state].append(expr['name'])
                            mapped = True
                            break

                    if not mapped:
                        suggestions['unmapped'].append(expr['name'])

                return suggestions

            except Exception as e:
                logger.error(f"Failed to create mapping suggestions for {psd_path}: {e}")
                raise

        return await loop.run_in_executor(self.executor, _suggest_mapping)

    async def create_component_organization(self, psd_path: str) -> Dict[str, List[str]]:
        """
        Create automatic component organization suggestions.

        Args:
            psd_path: Path to the PSD file

        Returns:
            Dictionary with suggested component organization by category
        """
        loop = asyncio.get_event_loop()

        def _organize_components():
            try:
                analyzer = PSDAnalyzer(psd_path)
                all_components = analyzer.find_all_components()

                # Convert to simple name lists for organization
                organization = {}
                for category, components in all_components.items():
                    if components:  # Only include categories with components
                        organization[category] = [comp["name"] for comp in components if comp["type"] == "LAYER"]

                return organization

            except Exception as e:
                logger.error(f"Failed to create component organization for {psd_path}: {e}")
                raise

        return await loop.run_in_executor(self.executor, _organize_components)

    def close(self):
        """Clean up the executor."""
        self.executor.shutdown(wait=True)