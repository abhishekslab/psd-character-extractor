"""
Command Line Interface for PSD Character Extractor

Provides command-line tools for analyzing and extracting characters from PSD files.
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

import click
from colorama import Fore, Style, init

from .analyzer import PSDAnalyzer
from .auto_mapper import AutoMapper
from .avatar_builder import AvatarBuilder
from .batch import BatchProcessor
from .extractor import CharacterExtractor
from .graph_builder import GraphBuilder
from .pcs_scanner import PCSScanner

# Initialize colorama for cross-platform colored output
init()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
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
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--quiet", "-q", is_flag=True, help="Suppress non-error output")
def cli(verbose: bool, quiet: bool) -> None:
    """PSD Character Extractor - Extract character expressions for VTubers and games."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    elif quiet:
        logging.getLogger().setLevel(logging.ERROR)


@cli.command()
@click.argument("psd_file", type=click.Path(exists=True, dir_okay=False))
@click.option("--detailed", "-d", is_flag=True, help="Show detailed layer analysis")
@click.option("--output", "-o", type=click.Path(), help="Save analysis to JSON file")
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
            click.echo(
                f"\n{Style.BRIGHT}Expression Layers ({len(expressions)}):{Style.RESET_ALL}"
            )
            for expr in expressions:
                keywords = ", ".join(expr["keywords"])
                click.echo(f"  • {expr['name']} (keywords: {keywords})")

            # Print layer groups
            groups = analysis["layer_groups"]
            click.echo(f"\n{Style.BRIGHT}Layer Groups:{Style.RESET_ALL}")
            for group_type, layers in groups.items():
                if layers:
                    click.echo(f"  {group_type.title()}: {len(layers)} layers")

            # Save to file if requested
            if output:
                with open(output, "w", encoding="utf-8") as f:
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
@click.argument("psd_file", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default="./output",
    help="Output directory for extracted images",
)
@click.option(
    "--mapping",
    "-m",
    type=click.Path(exists=True),
    help="JSON file with custom expression mapping",
)
@click.option(
    "--states",
    "-s",
    multiple=True,
    help="Specific lip sync states to extract (e.g., closed, small)",
)
@click.option("--prefix", "-p", default="character", help="Prefix for output filenames")
@click.option("--no-optimize", is_flag=True, help="Skip image optimization")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["png", "jpg", "webp"]),
    default="png",
    help="Output image format",
)
def extract(
    psd_file: str,
    output: str,
    mapping: Optional[str],
    states: tuple,
    prefix: str,
    no_optimize: bool,
    output_format: str,
) -> None:
    """Extract character expressions from PSD file."""
    try:
        print_info(f"Extracting from PSD file: {psd_file}")

        # Load custom mapping if provided
        custom_mapping = None
        if mapping:
            with open(mapping, "r", encoding="utf-8") as f:
                custom_mapping = json.load(f)
            print_info(f"Loaded custom mapping from {mapping}")

        # Initialize extractor
        extractor = CharacterExtractor(psd_file, custom_mapping)

        # Get extraction summary
        summary = extractor.get_extraction_summary()
        total_extractable = summary["total_extractable"]

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
            if output_format.lower() != "png":
                extractor.optimizer.format_type = output_format.upper()

        # Save expressions
        saved_files = extractor.save_expressions(
            expressions, output, optimize=not no_optimize, prefix=prefix
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
@click.argument("input_dir", type=click.Path(exists=True, file_okay=False))
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    required=True,
    help="Output directory for all extracted images",
)
@click.option(
    "--mapping",
    "-m",
    type=click.Path(exists=True),
    help="JSON file with expression mapping",
)
@click.option(
    "--workers", "-w", type=int, default=4, help="Number of concurrent workers"
)
@click.option("--report", is_flag=True, help="Generate processing report")
def batch(
    input_dir: str, output: str, mapping: Optional[str], workers: int, report: bool
) -> None:
    """Batch process multiple PSD files in a directory."""
    try:
        print_info(f"Starting batch processing: {input_dir}")

        # Initialize batch processor
        processor = BatchProcessor(
            input_dir=input_dir,
            output_dir=output,
            mapping_file=mapping,
            max_workers=workers,
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
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default="expression_mapping.json",
    help="Output file for the mapping template",
)
def create_mapping(output: str) -> None:
    """Create a template expression mapping file."""
    try:
        # Default mapping template with examples
        mapping_template = {
            "_comment": "Expression mapping for lip sync states",
            "_description": "Map lip sync states to PSD layer names",
            "closed": ["normal", "neutral", "smug", "calm"],
            "small": ["smile", "smile 2", "happy", "pleased"],
            "medium": ["delighted", "excited", "annoyed", "talking"],
            "wide": ["shocked", "surprised", "laugh", "amazed"],
            "_examples": {"custom_state": ["layer_name_1", "layer_name_2"]},
        }

        with open(output, "w", encoding="utf-8") as f:
            json.dump(mapping_template, f, indent=2, ensure_ascii=False)

        print_success(f"Expression mapping template created: {output}")
        print_info("Edit this file to match your PSD layer names")

    except Exception as e:
        print_error(f"Failed to create mapping template: {e}")
        sys.exit(1)


@cli.command()
@click.argument("psd_file", type=click.Path(exists=True, dir_okay=False))
def list_expressions(psd_file: str) -> None:
    """List all available expression layers in a PSD file."""
    try:
        print_info(f"Listing expressions in: {psd_file}")

        extractor = CharacterExtractor(psd_file)
        expressions = extractor.get_available_expressions()

        if not expressions:
            print_warning("No expression layers found")
            return

        click.echo(
            f"\n{Style.BRIGHT}Available Expressions ({len(expressions)}):{Style.RESET_ALL}"
        )
        for expr in expressions:
            click.echo(f"  • {expr}")

        # Show mapping possibilities
        summary = extractor.get_extraction_summary()
        mappable = summary["mappable_lip_sync_states"]

        if mappable:
            click.echo(f"\n{Style.BRIGHT}Mappable to Lip Sync States:{Style.RESET_ALL}")
            for state, expr_names in mappable.items():
                expr_list = ", ".join(expr_names)
                click.echo(f"  {state}: {expr_list}")

    except Exception as e:
        print_error(f"Failed to list expressions: {e}")
        sys.exit(1)


@cli.command()
@click.argument("psd_file", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    required=True,
    help="Output directory for avatar bundle",
)
@click.option(
    "--rules", type=click.Path(exists=True), help="YAML rules file for layer mapping"
)
@click.option("--name", help="Avatar name (defaults to PSD filename)")
@click.option(
    "--lang",
    type=click.Choice(["en", "jp"]),
    default="en",
    help="Language hint pack for mapping",
)
@click.option(
    "--strict", is_flag=True, help="Fail if essential visemes/states are missing"
)
def ingest(
    psd_file: str,
    output: str,
    rules: Optional[str],
    name: Optional[str],
    lang: str,
    strict: bool,
) -> None:
    """Convert PSD to standardized avatar bundle (JSON + PNG atlas)."""
    try:
        print_info(f"Processing PSD file: {psd_file}")

        # Build avatar bundle
        builder = AvatarBuilder(psd_file, output, rules)
        avatar = builder.build_avatar(name)

        # Save avatar bundle
        avatar_file = builder.save_avatar_bundle(avatar)
        print_success(f"Avatar bundle saved: {avatar_file}")

        # Generate report
        layers = builder.scanner.scan_layers()
        report_file = builder.generate_report(layers, avatar)
        print_success(f"Mapping report saved: {report_file}")

        # Check for warnings in strict mode
        if strict:
            report = builder.mapper.generate_mapping_report(layers, avatar)
            if report["warnings"]:
                print_error("Strict mode: Essential elements missing")
                for warning in report["warnings"]:
                    print_warning(warning)
                sys.exit(1)

        print_success(f"Avatar ingestion complete: {output}")

    except Exception as e:
        print_error(f"Ingestion failed: {e}")
        sys.exit(1)


@cli.command()
@click.argument("avatar_bundle", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--preset",
    type=click.Choice(["idle-talk", "full-emotion"]),
    default="idle-talk",
    help="Expression graph preset",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output file (defaults to graph.json in avatar directory)",
)
def graph(avatar_bundle: str, preset: str, output: Optional[str]) -> None:
    """Generate expression graph (state machine) for avatar."""
    try:
        print_info(f"Loading avatar bundle: {avatar_bundle}")

        # Load avatar bundle
        with open(avatar_bundle, "r", encoding="utf-8") as f:
            avatar_data = json.load(f)

        # Convert to AvatarBundle object (simplified loading)
        from .models.avatar import AvatarBundle, SlotDefinition

        avatar = AvatarBundle()

        # Load slots
        for slot_name, slot_data in avatar_data.get("slots", {}).items():
            slot_def = SlotDefinition(
                states=slot_data.get("states"),
                visemes=slot_data.get("visemes"),
                emotions=slot_data.get("emotions"),
                shapes=slot_data.get("shapes"),
            )
            avatar.slots[slot_name] = slot_def

        # Build graph
        builder = GraphBuilder(avatar)

        if preset == "idle-talk":
            graph = builder.build_idle_talk_graph()
        else:
            graph = builder.build_full_emotion_graph()

        # Determine output path
        if not output:
            bundle_dir = Path(avatar_bundle).parent
            output = str(bundle_dir / f"graph.{preset}.json")

        # Save graph
        graph_file = builder.save_graph(graph, Path(output).parent, Path(output).name)
        print_success(f"Expression graph saved: {graph_file}")

    except Exception as e:
        print_error(f"Graph generation failed: {e}")
        sys.exit(1)


@cli.command()
@click.argument("avatar_dir", type=click.Path(exists=True, file_okay=False))
@click.option("--port", type=int, default=8080, help="Preview server port")
@click.option("--open-browser", is_flag=True, help="Open browser automatically")
def preview(avatar_dir: str, port: int, open_browser: bool) -> None:
    """Preview avatar bundle with interactive demo."""
    try:
        avatar_path = Path(avatar_dir)

        # Check for required files
        avatar_json = avatar_path / "avatar.json"
        atlas_png = avatar_path / "atlas.png"

        if not avatar_json.exists():
            print_error(f"avatar.json not found in {avatar_dir}")
            sys.exit(1)

        if not atlas_png.exists():
            print_error(f"atlas.png not found in {avatar_dir}")
            sys.exit(1)

        print_info(f"Starting preview server for: {avatar_dir}")
        print_info(f"Server will be available at: http://localhost:{port}")

        # For now, just validate the files and show info
        with open(avatar_json, "r", encoding="utf-8") as f:
            avatar_data = json.load(f)

        print_success("Avatar bundle validation passed")
        print_info(f"Slots found: {len(avatar_data.get('slots', {}))}")
        print_info(f"Atlas: {atlas_png.name}")

        # Find graph files
        graph_files = list(avatar_path.glob("graph.*.json"))
        if graph_files:
            print_info(f"Expression graphs: {[f.name for f in graph_files]}")

        # TODO: Implement actual preview server with PixiJS demo
        print_warning("Interactive preview server not yet implemented")
        print_info("Use the generated files with your preferred avatar runtime")

    except Exception as e:
        print_error(f"Preview failed: {e}")
        sys.exit(1)


@cli.command()
@click.argument("psd_file", type=click.Path(exists=True, dir_okay=False))
@click.option("--detailed", is_flag=True, help="Show detailed PCS tag information")
def scan(psd_file: str, detailed: bool) -> None:
    """Scan PSD file with PCS (PSD Convention Standard) parser."""
    try:
        print_info(f"Scanning PSD file: {psd_file}")

        scanner = PCSScanner(psd_file)
        layers = scanner.scan_layers()

        print_success(f"Scanned {len(layers)} layers")

        # Show statistics
        stats = scanner.get_layer_statistics(layers)

        click.echo(f"\n{Style.BRIGHT}Layer Statistics:{Style.RESET_ALL}")
        click.echo(f"  Total layers: {stats['total_layers']}")
        click.echo(f"  Tagged layers: {stats['tagged_layers']}")

        if stats["groups"]:
            click.echo(f"\n{Style.BRIGHT}Groups:{Style.RESET_ALL}")
            for group, count in stats["groups"].items():
                click.echo(f"  {group}: {count} layers")

        if stats["parts"]:
            click.echo(f"\n{Style.BRIGHT}Parts:{Style.RESET_ALL}")
            for part, count in stats["parts"].items():
                click.echo(f"  {part}: {count} layers")

        if stats["visemes"]:
            click.echo(f"\n{Style.BRIGHT}Visemes found:{Style.RESET_ALL}")
            click.echo(f"  {', '.join(stats['visemes'])}")

        if stats["states"]:
            click.echo(f"\n{Style.BRIGHT}States found:{Style.RESET_ALL}")
            click.echo(f"  {', '.join(stats['states'])}")

        if detailed:
            click.echo(f"\n{Style.BRIGHT}Detailed Layer Information:{Style.RESET_ALL}")
            for layer in layers:
                if layer.pcs_tag:
                    tag_info = []
                    if layer.pcs_tag.group:
                        tag_info.append(f"group={layer.pcs_tag.group}")
                    if layer.pcs_tag.part:
                        tag_info.append(f"part={layer.pcs_tag.part}")
                    if layer.pcs_tag.side:
                        tag_info.append(f"side={layer.pcs_tag.side}")
                    if layer.pcs_tag.state:
                        tag_info.append(f"state={layer.pcs_tag.state}")
                    if layer.pcs_tag.viseme:
                        tag_info.append(f"viseme={layer.pcs_tag.viseme}")

                    tag_str = f" [{' '.join(tag_info)}]" if tag_info else ""
                    click.echo(f"  • {layer.name}{tag_str}")
                else:
                    click.echo(f"  • {layer.name} (untagged)")

    except Exception as e:
        print_error(f"Scan failed: {e}")
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


if __name__ == "__main__":
    cli()
