"""
Batch Processor

Handles batch processing of multiple PSD files and character extraction workflows.
"""

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional, Union

from tqdm import tqdm

from .analyzer import PSDAnalyzer
from .extractor import CharacterExtractor

logger = logging.getLogger(__name__)


class BatchProcessor:
    """Batch processor for multiple PSD files and extraction workflows."""

    def __init__(
        self,
        input_dir: Optional[str] = None,
        output_dir: Optional[str] = None,
        mapping_file: Optional[str] = None,
        max_workers: int = 4,
    ):
        """
        Initialize batch processor.

        Args:
            input_dir: Directory containing PSD files
            output_dir: Directory for output files
            mapping_file: JSON file containing expression mapping
            max_workers: Maximum number of concurrent workers
        """
        self.input_dir = Path(input_dir) if input_dir else None
        self.output_dir = Path(output_dir) if output_dir else None
        self.mapping_file = mapping_file
        self.max_workers = max_workers

        self.expression_mapping = None
        if mapping_file:
            self.load_expression_mapping(mapping_file)

    def load_expression_mapping(self, mapping_file: str) -> None:
        """
        Load expression mapping from JSON file.

        Args:
            mapping_file: Path to JSON file containing expression mapping
        """
        try:
            with open(mapping_file, "r", encoding="utf-8") as f:
                self.expression_mapping = json.load(f)
            logger.info(f"Loaded expression mapping from {mapping_file}")
        except Exception as e:
            logger.error(f"Failed to load expression mapping: {e}")
            raise

    def save_expression_mapping(
        self, mapping: Dict[str, List[str]], output_file: str
    ) -> None:
        """
        Save expression mapping to JSON file.

        Args:
            mapping: Expression mapping dictionary
            output_file: Path to output JSON file
        """
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(mapping, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved expression mapping to {output_file}")
        except Exception as e:
            logger.error(f"Failed to save expression mapping: {e}")

    def find_psd_files(self, directory: Optional[str] = None) -> List[Path]:
        """
        Find all PSD files in a directory.

        Args:
            directory: Directory to search (uses input_dir if None)

        Returns:
            List of Path objects for PSD files
        """
        search_dir = Path(directory) if directory else self.input_dir

        if not search_dir or not search_dir.exists():
            raise ValueError(f"Directory not found: {search_dir}")

        psd_files = list(search_dir.glob("*.psd")) + list(search_dir.glob("*.psb"))
        logger.info(f"Found {len(psd_files)} PSD files in {search_dir}")

        return psd_files

    def analyze_batch(
        self, psd_files: Optional[List[Union[str, Path]]] = None
    ) -> Dict[str, Dict]:
        """
        Analyze multiple PSD files to understand their structure.

        Args:
            psd_files: List of PSD file paths (finds automatically if None)

        Returns:
            Dictionary mapping file paths to analysis results
        """
        if psd_files is None:
            psd_files = self.find_psd_files()

        analysis_results = {}

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit analysis tasks
            future_to_file = {
                executor.submit(self._analyze_single_file, str(psd_file)): psd_file
                for psd_file in psd_files
            }

            # Collect results with progress bar
            for future in tqdm(
                as_completed(future_to_file),
                total=len(future_to_file),
                desc="Analyzing PSD files",
            ):
                psd_file = future_to_file[future]
                try:
                    result = future.result()
                    analysis_results[str(psd_file)] = result
                except Exception as e:
                    logger.error(f"Failed to analyze {psd_file}: {e}")
                    analysis_results[str(psd_file)] = {"error": str(e)}

        logger.info(f"Analyzed {len(analysis_results)} PSD files")
        return analysis_results

    def _analyze_single_file(self, psd_path: str) -> Dict:
        """
        Analyze a single PSD file.

        Args:
            psd_path: Path to PSD file

        Returns:
            Analysis results dictionary
        """
        try:
            analyzer = PSDAnalyzer(psd_path)
            return analyzer.analyze_layer_structure()
        except Exception as e:
            logger.error(f"Analysis failed for {psd_path}: {e}")
            return {"error": str(e)}

    def extract_batch(
        self,
        psd_files: Optional[List[Union[str, Path]]] = None,
        output_dir: Optional[str] = None,
        custom_mapping: Optional[Dict[str, List[str]]] = None,
    ) -> Dict[str, Dict]:
        """
        Extract expressions from multiple PSD files.

        Args:
            psd_files: List of PSD file paths
            output_dir: Output directory for extracted images
            custom_mapping: Custom expression mapping

        Returns:
            Dictionary mapping file paths to extraction results
        """
        if psd_files is None:
            psd_files = self.find_psd_files()

        if output_dir:
            self.output_dir = Path(output_dir)

        if not self.output_dir:
            raise ValueError("Output directory not specified")

        self.output_dir.mkdir(parents=True, exist_ok=True)

        mapping = custom_mapping or self.expression_mapping
        extraction_results = {}

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit extraction tasks
            future_to_file = {
                executor.submit(
                    self._extract_single_file, str(psd_file), mapping
                ): psd_file
                for psd_file in psd_files
            }

            # Collect results with progress bar
            for future in tqdm(
                as_completed(future_to_file),
                total=len(future_to_file),
                desc="Extracting characters",
            ):
                psd_file = future_to_file[future]
                try:
                    result = future.result()
                    extraction_results[str(psd_file)] = result
                except Exception as e:
                    logger.error(f"Failed to extract from {psd_file}: {e}")
                    extraction_results[str(psd_file)] = {"error": str(e)}

        logger.info(f"Extracted from {len(extraction_results)} PSD files")
        return extraction_results

    def _extract_single_file(
        self, psd_path: str, mapping: Optional[Dict[str, List[str]]]
    ) -> Dict:
        """
        Extract expressions from a single PSD file.

        Args:
            psd_path: Path to PSD file
            mapping: Expression mapping

        Returns:
            Extraction results dictionary
        """
        try:
            extractor = CharacterExtractor(psd_path, mapping)

            # Create output subdirectory for this character
            file_stem = Path(psd_path).stem
            char_output_dir = self.output_dir / file_stem
            char_output_dir.mkdir(exist_ok=True)

            # Extract and save expressions
            saved_files = extractor.extract_and_save(
                str(char_output_dir), custom_mapping=mapping, prefix=file_stem
            )

            # Get summary
            summary = extractor.get_extraction_summary()

            return {
                "success": True,
                "saved_files": saved_files,
                "summary": summary,
                "output_dir": str(char_output_dir),
            }

        except Exception as e:
            logger.error(f"Extraction failed for {psd_path}: {e}")
            return {"success": False, "error": str(e)}

    def generate_batch_report(
        self, results: Dict[str, Dict], output_file: Optional[str] = None
    ) -> str:
        """
        Generate a comprehensive batch processing report.

        Args:
            results: Results from batch processing
            output_file: Optional file to save report

        Returns:
            Report text
        """
        total_files = len(results)
        successful = sum(1 for r in results.values() if r.get("success", False))
        failed = total_files - successful

        report_lines = [
            "Batch Processing Report",
            "=" * 50,
            f"Total files processed: {total_files}",
            f"Successful extractions: {successful}",
            f"Failed extractions: {failed}",
            "",
            "Per-file Results:",
            "-" * 30,
        ]

        for file_path, result in results.items():
            file_name = Path(file_path).name
            if result.get("success", False):
                saved_count = len(result.get("saved_files", {}))
                report_lines.append(
                    f"✓ {file_name}: {saved_count} expressions extracted"
                )
            else:
                error = result.get("error", "Unknown error")
                report_lines.append(f"✗ {file_name}: {error}")

        report_text = "\n".join(report_lines)

        if output_file:
            try:
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(report_text)
                logger.info(f"Saved batch report to {output_file}")
            except Exception as e:
                logger.error(f"Failed to save report: {e}")

        return report_text

    def process_directory(
        self,
        input_dir: str,
        output_dir: str,
        mapping_file: Optional[str] = None,
        generate_report: bool = True,
    ) -> Dict[str, Dict]:
        """
        Complete batch processing workflow for a directory.

        Args:
            input_dir: Directory containing PSD files
            output_dir: Directory for output files
            mapping_file: Optional expression mapping file
            generate_report: Whether to generate processing report

        Returns:
            Complete processing results
        """
        # Update processor settings
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)

        if mapping_file:
            self.load_expression_mapping(mapping_file)

        # Find PSD files
        psd_files = self.find_psd_files()

        if not psd_files:
            logger.warning(f"No PSD files found in {input_dir}")
            return {}

        # Extract expressions
        results = self.extract_batch(psd_files)

        # Generate report if requested
        if generate_report:
            report_file = self.output_dir / "batch_report.txt"
            self.generate_batch_report(results, str(report_file))

        logger.info(f"Batch processing complete: {len(results)} files processed")
        return results
