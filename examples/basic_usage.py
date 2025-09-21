#!/usr/bin/env python3
"""
Basic Usage Examples for PSD Character Extractor

This script demonstrates the fundamental features of the PSD Character Extractor
library for extracting character expressions from PSD files.
"""

import json
import logging
from pathlib import Path

from psd_extractor import CharacterExtractor, PSDAnalyzer, BatchProcessor

# Configure logging to see what's happening
logging.basicConfig(level=logging.INFO)


def example_basic_extraction():
    """
    Example 1: Basic expression extraction

    Extract character expressions using the default lip sync mapping.
    """
    print("=== Example 1: Basic Expression Extraction ===")

    # Initialize the extractor with a PSD file
    psd_file = "character.psd"  # Replace with your PSD file path

    try:
        extractor = CharacterExtractor(psd_file)

        # Get a summary of what can be extracted
        summary = extractor.get_extraction_summary()
        print(f"Available expressions: {summary['available_expressions']}")
        print(f"Mappable lip sync states: {list(summary['mappable_lip_sync_states'].keys())}")

        # Extract expressions for all default lip sync states
        expressions = extractor.extract_expressions()
        print(f"Successfully extracted {len(expressions)} expressions")

        # Save expressions to files
        output_dir = "./basic_output"
        saved_files = extractor.save_expressions(expressions, output_dir)

        print("Saved files:")
        for state, file_path in saved_files.items():
            print(f"  {state}: {file_path}")

    except Exception as e:
        print(f"Error: {e}")
        print("Make sure you have a valid PSD file named 'character.psd'")


def example_custom_mapping():
    """
    Example 2: Using custom expression mapping

    Create and use a custom mapping for specific use cases.
    """
    print("\n=== Example 2: Custom Expression Mapping ===")

    # Define custom mapping for game dialogue system
    game_mapping = {
        'happy': ['smile', 'delighted', 'laugh'],
        'neutral': ['normal', 'calm'],
        'surprised': ['shocked', 'amazed'],
        'sad': ['sad', 'disappointed'],  # These might not exist in your PSD
    }

    psd_file = "character.psd"

    try:
        extractor = CharacterExtractor(psd_file, game_mapping)

        # Extract using custom mapping
        expressions = extractor.extract_expressions()

        # Save with custom prefix
        output_dir = "./game_characters"
        saved_files = extractor.save_expressions(
            expressions,
            output_dir,
            prefix="game_character"
        )

        print("Game character expressions saved:")
        for emotion, file_path in saved_files.items():
            print(f"  {emotion}: {file_path}")

    except Exception as e:
        print(f"Error: {e}")


def example_selective_extraction():
    """
    Example 3: Extract only specific expressions

    Sometimes you only need certain expressions, not all of them.
    """
    print("\n=== Example 3: Selective Expression Extraction ===")

    psd_file = "character.psd"

    try:
        extractor = CharacterExtractor(psd_file)

        # Only extract closed and small mouth states (for basic lip sync)
        target_states = ['closed', 'small']
        expressions = extractor.extract_expressions(target_states=target_states)

        print(f"Extracted {len(expressions)} expressions: {list(expressions.keys())}")

        # Save to a specific directory
        output_dir = "./minimal_lipSync"
        saved_files = extractor.save_expressions(expressions, output_dir)

        print("Minimal lip sync set saved:")
        for state, file_path in saved_files.items():
            print(f"  {state}: {file_path}")

    except Exception as e:
        print(f"Error: {e}")


def example_optimization_options():
    """
    Example 4: Different optimization and format options

    Demonstrate various image optimization and output format options.
    """
    print("\n=== Example 4: Optimization and Format Options ===")

    psd_file = "character.psd"

    try:
        extractor = CharacterExtractor(psd_file)
        expressions = extractor.extract_expressions()

        # Option 1: High-quality PNG (default)
        print("Saving high-quality PNG versions...")
        extractor.save_expressions(
            expressions,
            "./high_quality",
            optimize=True,
            prefix="hq"
        )

        # Option 2: Fast extraction without optimization
        print("Saving raw versions (no optimization)...")
        extractor.save_expressions(
            expressions,
            "./raw_output",
            optimize=False,
            prefix="raw"
        )

        # Option 3: Web-optimized with custom settings
        print("Saving web-optimized versions...")
        # Configure optimizer for web use
        extractor.optimizer.set_target_size(300, 400)  # Smaller size
        extractor.optimizer.set_quality(75)  # Lower quality for smaller files
        extractor.optimizer.format_type = "JPEG"

        extractor.save_expressions(
            expressions,
            "./web_optimized",
            optimize=True,
            prefix="web"
        )

    except Exception as e:
        print(f"Error: {e}")


def example_psd_analysis():
    """
    Example 5: Analyzing PSD structure

    Before extraction, analyze the PSD to understand its structure.
    """
    print("\n=== Example 5: PSD Structure Analysis ===")

    psd_file = "character.psd"

    try:
        analyzer = PSDAnalyzer(psd_file)

        # Get basic information
        basic_info = analyzer.get_basic_info()
        print(f"PSD Dimensions: {basic_info['width']} x {basic_info['height']}")
        print(f"Total Layers: {basic_info['total_layers']}")

        # Find expression layers
        expressions = analyzer.find_expression_layers()
        print(f"\nFound {len(expressions)} potential expression layers:")
        for expr in expressions:
            keywords = ", ".join(expr['keywords'])
            print(f"  - {expr['name']} (keywords: {keywords})")

        # Get layer groups
        analysis = analyzer.analyze_layer_structure()
        layer_groups = analysis['layer_groups']
        print(f"\nLayer organization:")
        for group_type, layers in layer_groups.items():
            if layers:
                print(f"  {group_type.title()}: {len(layers)} layers")

        # Save detailed analysis to JSON
        output_file = "psd_analysis.json"
        with open(output_file, 'w') as f:
            json.dump(analysis, f, indent=2, default=str)
        print(f"\nDetailed analysis saved to: {output_file}")

    except Exception as e:
        print(f"Error: {e}")


def example_batch_processing():
    """
    Example 6: Batch processing multiple PSD files

    Process multiple character PSD files at once.
    """
    print("\n=== Example 6: Batch Processing ===")

    # Create batch processor
    processor = BatchProcessor(
        input_dir="./psd_files",      # Directory with PSD files
        output_dir="./batch_output",  # Output directory
        max_workers=2                 # Number of parallel workers
    )

    try:
        # Find all PSD files in the input directory
        psd_files = processor.find_psd_files()
        print(f"Found {len(psd_files)} PSD files to process")

        if psd_files:
            # Extract expressions from all files
            results = processor.extract_batch()

            # Count successful extractions
            successful = sum(1 for r in results.values() if r.get("success", False))
            total = len(results)

            print(f"Batch processing complete: {successful}/{total} files successful")

            # Generate a report
            report = processor.generate_batch_report(results, "batch_report.txt")
            print("Batch report saved to: batch_report.txt")

    except Exception as e:
        print(f"Error: {e}")
        print("Make sure you have a './psd_files' directory with some PSD files")


def example_all_expressions():
    """
    Example 7: Extract all available expressions (not just lip sync)

    Sometimes you want every expression, not just the ones mapped to lip sync.
    """
    print("\n=== Example 7: Extract All Available Expressions ===")

    psd_file = "character.psd"

    try:
        extractor = CharacterExtractor(psd_file)

        # Get list of all available expressions
        available = extractor.get_available_expressions()
        print(f"Available expressions: {available}")

        # Extract all expressions (not just lip sync mapped ones)
        all_expressions = extractor.extract_all_expressions()

        print(f"Successfully extracted {len(all_expressions)} total expressions")

        # Save all expressions
        output_dir = "./all_expressions"
        saved_files = extractor.save_expressions(
            all_expressions,
            output_dir,
            prefix="all"
        )

        print("All expressions saved:")
        for name, file_path in saved_files.items():
            print(f"  {name}: {file_path}")

    except Exception as e:
        print(f"Error: {e}")


def main():
    """
    Run all examples (comment out any you don't want to run)
    """
    print("PSD Character Extractor - Basic Usage Examples")
    print("=" * 50)

    # Note: Make sure you have a PSD file named 'character.psd' in the current directory
    # or modify the psd_file variable in each example to point to your PSD file

    example_basic_extraction()
    example_custom_mapping()
    example_selective_extraction()
    example_optimization_options()
    example_psd_analysis()
    example_batch_processing()
    example_all_expressions()

    print("\n" + "=" * 50)
    print("All examples completed!")
    print("\nNext steps:")
    print("1. Check the output directories for extracted images")
    print("2. Review the analysis JSON files")
    print("3. Modify the examples for your specific use case")


if __name__ == "__main__":
    main()