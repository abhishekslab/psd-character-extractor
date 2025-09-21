"""
Command Line Interface for PSD Character Extractor

Provides command-line tools for analyzing and extracting characters from PSD files.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional

import click
from colorama import init, Fore, Style

from .analyzer import PSDAnalyzer
from .extractor import CharacterExtractor
from .batch import BatchProcessor

# Initialize colorama for cross-platform colored output
init()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_success(message: str) -> None:
    """Print success message in green."""
    click.echo(f"{Fore.GREEN}✓ {message}{Style.RESET_ALL}")


def print_error(message: str) -> None:
    """Print error message in red."""
    click.echo(f"{Fore.RED}✗ {message}{Style.RESET_ALL}")


def print_warning(message: str) -> None:
    """Print warning message in yellow."""
    click.echo(f"{Fore.YELLOW}⚠ {message}{Style.RESET_ALL}")


def print_info(message: str) -> None:
    """Print info message in blue."""
    click.echo(f"{Fore.BLUE}ℹ {message}{Style.RESET_ALL}")


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--quiet', '-q', is_flag=True, help='Suppress non-error output')
def cli(verbose: bool, quiet: bool) -> None:
    """PSD Character Extractor - Extract character expressions for VTubers and games."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    elif quiet:
        logging.getLogger().setLevel(logging.ERROR)


@cli.command()
@click.argument('psd_file', type=click.Path(exists=True, dir_okay=False))
@click.option('--detailed', '-d', is_flag=True, help='Show detailed layer analysis')
@click.option('--output', '-o', type=click.Path(), help='Save analysis to JSON file')
def analyze(psd_file: str, detailed: bool, output: Optional[str]) -> None:
    """Analyze PSD file structure and identify expression layers."""
    try:
        print_info(f"Analyzing PSD file: {psd_file}")

        analyzer = PSDAnalyzer(psd_file)

        if detailed:
            # Full detailed analysis
            analysis = analyzer.analyze_layer_structure()

            # Print basic info
            info = analysis["basic_info"]
            click.echo(f"\n{Style.BRIGHT}PSD Information:{Style.RESET_ALL}")
            click.echo(f"  Dimensions: {info['width']} x {info['height']}")
            click.echo(f"  Total Layers: {info['total_layers']}")

            # Print expression layers
            expressions = analysis["expression_analysis"]
            click.echo(f"\n{Style.BRIGHT}Expression Layers ({len(expressions)}):{Style.RESET_ALL}")
            for expr in expressions:
                keywords = ", ".join(expr['keywords'])
                click.echo(f"  • {expr['name']} (keywords: {keywords})")

            # Print layer groups
            groups = analysis["layer_groups"]
            click.echo(f"\n{Style.BRIGHT}Layer Groups:{Style.RESET_ALL}")
            for group_type, layers in groups.items():
                if layers:
                    click.echo(f"  {group_type.title()}: {len(layers)} layers")

            # Save to file if requested
            if output:
                with open(output, 'w', encoding='utf-8') as f:
                    json.dump(analysis, f, indent=2, default=str)
                print_success(f"Analysis saved to {output}")

        else:
            # Simple analysis
            analyzer.print_analysis_report()

        print_success("Analysis complete")

    except Exception as e:
        print_error(f"Analysis failed: {e}")
        sys.exit(1)


@cli.command()
@click.argument('psd_file', type=click.Path(exists=True, dir_okay=False))
@click.option('--output', '-o', type=click.Path(), default='./output',
              help='Output directory for extracted images')
@click.option('--mapping', '-m', type=click.Path(exists=True),
              help='JSON file with custom expression mapping')
@click.option('--states', '-s', multiple=True,
              help='Specific lip sync states to extract (e.g., closed, small)')
@click.option('--prefix', '-p', default='character',
              help='Prefix for output filenames')
@click.option('--no-optimize', is_flag=True,
              help='Skip image optimization')
@click.option('--format', 'output_format', type=click.Choice(['png', 'jpg', 'webp']),
              default='png', help='Output image format')
def extract(psd_file: str, output: str, mapping: Optional[str],
           states: tuple, prefix: str, no_optimize: bool, output_format: str) -> None:
    """Extract character expressions from PSD file."""
    try:
        print_info(f"Extracting from PSD file: {psd_file}")

        # Load custom mapping if provided
        custom_mapping = None
        if mapping:
            with open(mapping, 'r', encoding='utf-8') as f:
                custom_mapping = json.load(f)
            print_info(f"Loaded custom mapping from {mapping}")

        # Initialize extractor
        extractor = CharacterExtractor(psd_file, custom_mapping)

        # Get extraction summary
        summary = extractor.get_extraction_summary()
        total_extractable = summary['total_extractable']

        if total_extractable == 0:
            print_warning("No extractable expressions found")
            return

        print_info(f"Found {total_extractable} extractable lip sync states")

        # Extract expressions
        target_states = list(states) if states else None
        expressions = extractor.extract_expressions(target_states=target_states)

        if not expressions:
            print_error("No expressions could be extracted")
            return

        # Configure optimizer if needed
        if not no_optimize:
            if output_format.lower() != 'png':
                extractor.optimizer.format_type = output_format.upper()

        # Save expressions
        saved_files = extractor.save_expressions(
            expressions,
            output,
            optimize=not no_optimize,
            prefix=prefix
        )

        # Report results
        print_success(f"Successfully extracted {len(saved_files)} expressions:")
        for state, file_path in saved_files.items():
            click.echo(f"  • {state}: {file_path}")

        print_success(f"Output saved to: {output}")

    except Exception as e:
        print_error(f"Extraction failed: {e}")
        sys.exit(1)


@cli.command()
@click.argument('input_dir', type=click.Path(exists=True, file_okay=False))
@click.option('--output', '-o', type=click.Path(), required=True,
              help='Output directory for all extracted images')
@click.option('--mapping', '-m', type=click.Path(exists=True),
              help='JSON file with expression mapping')
@click.option('--workers', '-w', type=int, default=4,
              help='Number of concurrent workers')
@click.option('--report', is_flag=True,
              help='Generate processing report')
def batch(input_dir: str, output: str, mapping: Optional[str],
         workers: int, report: bool) -> None:
    """Batch process multiple PSD files in a directory."""
    try:
        print_info(f"Starting batch processing: {input_dir}")

        # Initialize batch processor
        processor = BatchProcessor(
            input_dir=input_dir,
            output_dir=output,
            mapping_file=mapping,
            max_workers=workers
        )

        # Find PSD files
        psd_files = processor.find_psd_files()

        if not psd_files:
            print_warning(f"No PSD files found in {input_dir}")
            return

        print_info(f"Found {len(psd_files)} PSD files to process")

        # Process all files
        results = processor.extract_batch()

        # Count results
        successful = sum(1 for r in results.values() if r.get("success", False))
        total = len(results)

        if successful == total:
            print_success(f"All {total} files processed successfully")
        elif successful > 0:
            print_warning(f"{successful}/{total} files processed successfully")
        else:
            print_error(f"All {total} files failed to process")

        # Generate report if requested
        if report:
            report_file = Path(output) / "batch_report.txt"
            processor.generate_batch_report(results, str(report_file))
            print_success(f"Report saved to: {report_file}")

        print_success(f"Batch processing complete. Output in: {output}")

    except Exception as e:
        print_error(f"Batch processing failed: {e}")
        sys.exit(1)


@cli.command()
@click.option('--output', '-o', type=click.Path(), default='expression_mapping.json',
              help='Output file for the mapping template')
def create_mapping(output: str) -> None:
    """Create a template expression mapping file."""
    try:
        # Default mapping template with examples
        mapping_template = {
            "_comment": "Expression mapping for lip sync states",
            "_description": "Map lip sync states to PSD layer names",
            "closed": [
                "normal",
                "neutral",
                "smug",
                "calm"
            ],
            "small": [
                "smile",
                "smile 2",
                "happy",
                "pleased"
            ],
            "medium": [
                "delighted",
                "excited",
                "annoyed",
                "talking"
            ],
            "wide": [
                "shocked",
                "surprised",
                "laugh",
                "amazed"
            ],
            "_examples": {
                "custom_state": [
                    "layer_name_1",
                    "layer_name_2"
                ]
            }
        }

        with open(output, 'w', encoding='utf-8') as f:
            json.dump(mapping_template, f, indent=2, ensure_ascii=False)

        print_success(f"Expression mapping template created: {output}")
        print_info("Edit this file to match your PSD layer names")

    except Exception as e:
        print_error(f"Failed to create mapping template: {e}")
        sys.exit(1)


@cli.command()
@click.argument('psd_file', type=click.Path(exists=True, dir_okay=False))
def list_expressions(psd_file: str) -> None:
    """List all available expression layers in a PSD file."""
    try:
        print_info(f"Listing expressions in: {psd_file}")

        extractor = CharacterExtractor(psd_file)
        expressions = extractor.get_available_expressions()

        if not expressions:
            print_warning("No expression layers found")
            return

        click.echo(f"\n{Style.BRIGHT}Available Expressions ({len(expressions)}):{Style.RESET_ALL}")
        for expr in expressions:
            click.echo(f"  • {expr}")

        # Show mapping possibilities
        summary = extractor.get_extraction_summary()
        mappable = summary['mappable_lip_sync_states']

        if mappable:
            click.echo(f"\n{Style.BRIGHT}Mappable to Lip Sync States:{Style.RESET_ALL}")
            for state, expr_names in mappable.items():
                expr_list = ", ".join(expr_names)
                click.echo(f"  {state}: {expr_list}")

    except Exception as e:
        print_error(f"Failed to list expressions: {e}")
        sys.exit(1)


# Entry points for console scripts
def extract_command():
    """Entry point for psd-extract command."""
    extract()


def analyze_command():
    """Entry point for psd-analyze command."""
    analyze()


def batch_command():
    """Entry point for psd-batch command."""
    batch()


if __name__ == '__main__':
    cli()