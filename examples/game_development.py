#!/usr/bin/env python3
"""
Game Development Integration Examples

This script demonstrates how to use PSD Character Extractor
for game development workflows, including dialogue systems,
character animations, and asset pipeline integration.
"""

import json
import csv
import logging
from pathlib import Path
from typing import Dict, List, Any

from psd_extractor import CharacterExtractor, BatchProcessor, ImageOptimizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GameCharacterPipeline:
    """
    Game development pipeline for character asset creation
    """

    def __init__(self, game_name: str = "MyGame", base_output_dir: str = "./game_assets"):
        self.game_name = game_name
        self.base_output_dir = Path(base_output_dir)
        self.characters_dir = self.base_output_dir / "characters"
        self.config_dir = self.base_output_dir / "config"

        # Create directories
        self.characters_dir.mkdir(parents=True, exist_ok=True)
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def process_character(self, psd_file: str, character_name: str, character_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single character PSD file for game use

        Args:
            psd_file: Path to character PSD file
            character_name: Name of the character in the game
            character_config: Character-specific configuration

        Returns:
            Dictionary with processing results
        """
        logger.info(f"Processing character: {character_name}")

        # Create character output directory
        char_dir = self.characters_dir / character_name
        char_dir.mkdir(exist_ok=True)

        # Initialize extractor with game-specific mapping
        game_mapping = character_config.get('expression_mapping', {
            'neutral': ['normal', 'calm', 'idle'],
            'happy': ['smile', 'delighted', 'joy'],
            'sad': ['sad', 'disappointed', 'crying'],
            'angry': ['angry', 'annoyed', 'mad'],
            'surprised': ['shocked', 'surprised', 'amazed'],
            'talking': ['talking', 'speaking', 'medium']
        })

        extractor = CharacterExtractor(psd_file, game_mapping)

        # Configure optimizer for game assets
        optimizer = ImageOptimizer(
            target_width=character_config.get('width', 512),
            target_height=character_config.get('height', 768),
            quality=character_config.get('quality', 90),
            format_type=character_config.get('format', 'PNG')
        )
        extractor.optimizer = optimizer

        # Extract expressions
        expressions = extractor.extract_expressions()

        # Save expressions
        saved_files = extractor.save_expressions(
            expressions,
            str(char_dir),
            prefix=character_name.lower()
        )

        # Generate character metadata
        metadata = {
            'character_name': character_name,
            'source_psd': psd_file,
            'expressions': saved_files,
            'config': character_config,
            'asset_info': {
                'format': character_config.get('format', 'PNG'),
                'dimensions': f"{character_config.get('width', 512)}x{character_config.get('height', 768)}",
                'has_transparency': True if character_config.get('format', 'PNG') == 'PNG' else False
            }
        }

        # Save character metadata
        metadata_path = char_dir / f"{character_name.lower()}_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Character {character_name} processed: {len(saved_files)} expressions")
        return metadata


def example_dialogue_system_setup():
    """
    Example: Setup character assets for a dialogue system

    This example shows how to prepare character expressions
    for a typical game dialogue system.
    """
    print("=== Dialogue System Setup Example ===")

    # Game configuration
    game_config = {
        'characters': {
            'protagonist': {
                'psd_file': 'protagonist.psd',
                'width': 400,
                'height': 600,
                'format': 'PNG',
                'expression_mapping': {
                    'neutral': ['normal', 'calm'],
                    'happy': ['smile', 'joy'],
                    'concerned': ['worried', 'anxious'],
                    'determined': ['serious', 'focused'],
                    'surprised': ['shocked', 'amazed']
                }
            },
            'companion': {
                'psd_file': 'companion.psd',
                'width': 400,
                'height': 600,
                'format': 'PNG',
                'expression_mapping': {
                    'cheerful': ['smile', 'happy'],
                    'sarcastic': ['smug', 'sly'],
                    'worried': ['concerned', 'anxious'],
                    'excited': ['delighted', 'enthusiastic']
                }
            }
        }
    }

    try:
        pipeline = GameCharacterPipeline("DialogueGame", "./dialogue_assets")

        processed_characters = {}

        for char_name, char_config in game_config['characters'].items():
            try:
                metadata = pipeline.process_character(
                    char_config['psd_file'],
                    char_name,
                    char_config
                )
                processed_characters[char_name] = metadata
            except Exception as e:
                print(f"Failed to process {char_name}: {e}")
                continue

        # Generate dialogue system configuration
        dialogue_config = {
            'game': 'DialogueGame',
            'characters': processed_characters,
            'dialogue_states': {
                'neutral': 'Default state for normal conversation',
                'happy': 'Use for positive responses',
                'concerned': 'Use for worried or uncertain dialogue',
                'surprised': 'Use for unexpected revelations'
            }
        }

        config_path = pipeline.config_dir / "dialogue_config.json"
        with open(config_path, 'w') as f:
            json.dump(dialogue_config, f, indent=2)

        print(f"Dialogue system assets created for {len(processed_characters)} characters")
        print(f"Configuration saved: {config_path}")

        # Create a simple dialogue script example
        script_example = """# Example Dialogue Script
# Format: CHARACTER: expression: "dialogue text"

SCENE: Village Square

protagonist: neutral: "Have you seen anything strange around here lately?"
companion: sarcastic: "You mean besides you talking to every villager we meet?"
protagonist: concerned: "I'm serious. Something feels off about this place."
companion: worried: "Now that you mention it... yeah, I feel it too."
protagonist: determined: "We need to investigate. Stay close."
companion: cheerful: "Lead the way, fearless leader!"
"""

        script_path = pipeline.config_dir / "example_dialogue.txt"
        with open(script_path, 'w') as f:
            f.write(script_example)

        print(f"Example dialogue script: {script_path}")

    except Exception as e:
        print(f"Error: {e}")


def example_rpg_character_roster():
    """
    Example: Create a complete character roster for an RPG

    This example shows batch processing of multiple characters
    with different roles and expression sets.
    """
    print("\n=== RPG Character Roster Example ===")

    # RPG character configuration
    rpg_characters = {
        'hero': {
            'role': 'protagonist',
            'expressions': ['brave', 'determined', 'happy', 'sad', 'angry'],
            'size': 'large'  # Main character gets larger sprites
        },
        'mage': {
            'role': 'party_member',
            'expressions': ['wise', 'mysterious', 'concerned', 'casting'],
            'size': 'medium'
        },
        'rogue': {
            'role': 'party_member',
            'expressions': ['sly', 'sneaky', 'surprised', 'smug'],
            'size': 'medium'
        },
        'merchant': {
            'role': 'npc',
            'expressions': ['friendly', 'greedy', 'suspicious'],
            'size': 'small'
        }
    }

    # Size configurations
    size_configs = {
        'large': {'width': 600, 'height': 900, 'quality': 95},
        'medium': {'width': 400, 'height': 600, 'quality': 90},
        'small': {'width': 300, 'height': 450, 'quality': 85}
    }

    try:
        pipeline = GameCharacterPipeline("RPGGame", "./rpg_assets")

        # Process each character
        roster_data = {}

        for char_name, char_info in rpg_characters.items():
            psd_file = f"{char_name}.psd"  # Assuming PSD files are named after characters

            # Get size configuration
            size_config = size_configs[char_info['size']]

            # Create expression mapping based on character role
            expression_mapping = {}
            for expr in char_info['expressions']:
                # Map each desired expression to possible PSD layer names
                expression_mapping[expr] = [expr, expr.capitalize(), expr.upper()]

            char_config = {
                'role': char_info['role'],
                'expression_mapping': expression_mapping,
                **size_config,
                'format': 'PNG'
            }

            try:
                metadata = pipeline.process_character(psd_file, char_name, char_config)
                roster_data[char_name] = metadata
                print(f"✓ Processed {char_name} ({char_info['role']})")
            except Exception as e:
                print(f"✗ Failed to process {char_name}: {e}")

        # Generate RPG roster configuration
        rpg_config = {
            'game_title': 'RPGGame',
            'character_roster': roster_data,
            'role_categories': {
                'protagonist': [name for name, info in rpg_characters.items() if info['role'] == 'protagonist'],
                'party_members': [name for name, info in rpg_characters.items() if info['role'] == 'party_member'],
                'npcs': [name for name, info in rpg_characters.items() if info['role'] == 'npc']
            },
            'asset_guidelines': {
                'protagonist': 'Large, high-quality sprites for cutscenes',
                'party_member': 'Medium sprites for dialogue and battle',
                'npc': 'Small sprites for world interactions'
            }
        }

        config_path = pipeline.config_dir / "rpg_roster.json"
        with open(config_path, 'w') as f:
            json.dump(rpg_config, f, indent=2)

        print(f"\nRPG character roster complete: {len(roster_data)} characters processed")
        print(f"Roster configuration: {config_path}")

    except Exception as e:
        print(f"Error: {e}")


def example_visual_novel_setup():
    """
    Example: Setup for visual novel character expressions

    Visual novels typically need many subtle expressions
    for emotional storytelling.
    """
    print("\n=== Visual Novel Setup Example ===")

    # Visual novel requires more nuanced expressions
    vn_expression_mapping = {
        # Basic emotions
        'neutral': ['normal', 'calm', 'default'],
        'happy': ['smile', 'joy', 'cheerful'],
        'sad': ['sad', 'melancholy', 'crying'],
        'angry': ['angry', 'furious', 'mad'],

        # Subtle emotions
        'shy': ['shy', 'bashful', 'embarrassed'],
        'confident': ['confident', 'proud', 'smug'],
        'worried': ['worried', 'anxious', 'concerned'],
        'surprised': ['surprised', 'shocked', 'amazed'],
        'confused': ['confused', 'puzzled', 'questioning'],
        'determined': ['determined', 'serious', 'focused'],

        # Speaking states
        'speaking': ['talking', 'explaining', 'medium'],
        'shouting': ['yelling', 'loud', 'wide'],
        'whispering': ['quiet', 'soft', 'small'],

        # Special states
        'blushing': ['blushing', 'flustered', 'red'],
        'sleeping': ['sleeping', 'tired', 'closed_eyes'],
        'thinking': ['contemplating', 'pondering', 'thoughtful']
    }

    try:
        # High-quality settings for visual novels
        vn_config = {
            'width': 800,
            'height': 1200,
            'quality': 95,
            'format': 'PNG',
            'expression_mapping': vn_expression_mapping
        }

        pipeline = GameCharacterPipeline("VisualNovel", "./vn_assets")

        # Process main character
        psd_file = "vn_character.psd"  # Replace with actual file
        character_name = "protagonist"

        try:
            metadata = pipeline.process_character(psd_file, character_name, vn_config)

            # Create character state database for visual novel engine
            character_db = {
                'character_id': character_name,
                'display_name': character_name.title(),
                'asset_path': f"characters/{character_name}/",
                'expressions': {}
            }

            for state, file_path in metadata['expressions'].items():
                character_db['expressions'][state] = {
                    'file': Path(file_path).name,
                    'description': f"{state.title()} expression",
                    'emotional_value': 0.5,  # Placeholder for emotion system
                    'usage_context': f"Use for {state} emotional scenes"
                }

            # Save character database
            db_path = pipeline.config_dir / f"{character_name}_database.json"
            with open(db_path, 'w') as f:
                json.dump(character_db, f, indent=2)

            # Create expression usage guide
            guide_content = f"""# Visual Novel Expression Guide - {character_name.title()}

## Available Expressions: {len(metadata['expressions'])}

### Basic Emotions
- neutral: Default state for normal scenes
- happy: Positive moments, good news
- sad: Emotional scenes, bad news
- angry: Conflict scenes, arguments

### Subtle Emotions
- shy: Romance scenes, embarrassment
- confident: Success moments, declarations
- worried: Tension scenes, uncertainty
- surprised: Plot twists, revelations

### Dialogue States
- speaking: Normal conversation
- shouting: Intense dialogue, arguments
- whispering: Intimate or secret conversations

### Special States
- blushing: Romance scenes
- sleeping: Rest scenes, dream sequences
- thinking: Internal monologue, decisions

## Usage in Visual Novel Script

Example script format:
```
@character {character_name} expression happy
{character_name}: "I'm so excited about this!"

@character {character_name} expression worried
{character_name}: "But what if something goes wrong?"
```

## Integration Notes
1. Load all expressions at startup for smooth transitions
2. Use fade transitions between expressions (200ms recommended)
3. Consider expression inheritance (sad -> crying -> sobbing)
4. Implement expression queuing for rapid dialogue
"""

            guide_path = pipeline.config_dir / f"{character_name}_expression_guide.md"
            with open(guide_path, 'w') as f:
                f.write(guide_content)

            print(f"Visual novel character setup complete")
            print(f"Expressions: {len(metadata['expressions'])}")
            print(f"Database: {db_path}")
            print(f"Guide: {guide_path}")

        except Exception as e:
            print(f"Failed to process character: {e}")

    except Exception as e:
        print(f"Error: {e}")


def example_asset_validation():
    """
    Example: Validate and verify generated game assets

    This example shows how to verify that all required
    assets were generated correctly.
    """
    print("\n=== Asset Validation Example ===")

    def validate_character_assets(character_dir: Path, required_expressions: List[str]) -> Dict[str, Any]:
        """Validate that a character has all required expressions"""
        validation_result = {
            'character': character_dir.name,
            'valid': True,
            'missing_expressions': [],
            'extra_files': [],
            'file_info': {}
        }

        # Check for required expressions
        for expr in required_expressions:
            # Look for files matching the expression pattern
            expr_files = list(character_dir.glob(f"*{expr}*"))
            if not expr_files:
                validation_result['missing_expressions'].append(expr)
                validation_result['valid'] = False
            else:
                # Get file info
                expr_file = expr_files[0]  # Take first match
                stat = expr_file.stat()
                validation_result['file_info'][expr] = {
                    'file': expr_file.name,
                    'size_kb': round(stat.st_size / 1024, 2),
                    'exists': True
                }

        # Check for unexpected files
        all_files = [f for f in character_dir.iterdir() if f.is_file() and f.suffix.lower() in ['.png', '.jpg', '.jpeg']]
        expected_files = len(required_expressions)
        if len(all_files) > expected_files:
            extra_count = len(all_files) - expected_files
            validation_result['extra_files'] = [f.name for f in all_files[expected_files:]]

        return validation_result

    try:
        # Define required expressions for different game types
        game_requirements = {
            'dialogue_game': ['neutral', 'happy', 'concerned', 'surprised'],
            'rpg': ['brave', 'determined', 'happy', 'sad', 'angry'],
            'visual_novel': ['neutral', 'happy', 'sad', 'shy', 'confident']
        }

        # Validate assets for each game type
        validation_results = {}

        for game_type, required_exprs in game_requirements.items():
            game_dir = Path(f"./{game_type.replace('_', '')}_assets/characters")

            if game_dir.exists():
                game_validation = {
                    'game_type': game_type,
                    'characters': {},
                    'overall_valid': True
                }

                # Check each character directory
                for char_dir in game_dir.iterdir():
                    if char_dir.is_dir():
                        char_result = validate_character_assets(char_dir, required_exprs)
                        game_validation['characters'][char_dir.name] = char_result

                        if not char_result['valid']:
                            game_validation['overall_valid'] = False

                validation_results[game_type] = game_validation

        # Print validation report
        print("Asset Validation Report")
        print("=" * 40)

        for game_type, results in validation_results.items():
            print(f"\n{game_type.title()}:")
            print(f"  Overall Valid: {'✓' if results['overall_valid'] else '✗'}")

            for char_name, char_result in results['characters'].items():
                status = '✓' if char_result['valid'] else '✗'
                print(f"  {status} {char_name}")

                if char_result['missing_expressions']:
                    print(f"    Missing: {', '.join(char_result['missing_expressions'])}")

                if char_result['extra_files']:
                    print(f"    Extra files: {len(char_result['extra_files'])}")

        # Save detailed validation report
        report_path = Path("./asset_validation_report.json")
        with open(report_path, 'w') as f:
            json.dump(validation_results, f, indent=2)

        print(f"\nDetailed validation report saved: {report_path}")

    except Exception as e:
        print(f"Validation error: {e}")


def main():
    """
    Run all game development examples
    """
    print("PSD Character Extractor - Game Development Examples")
    print("=" * 60)

    # Note: These examples assume you have PSD files with appropriate names
    # Modify the file paths in each example to match your actual PSD files

    example_dialogue_system_setup()
    example_rpg_character_roster()
    example_visual_novel_setup()
    example_asset_validation()

    print("\n" + "=" * 60)
    print("All game development examples completed!")
    print("\nNext steps for game integration:")
    print("1. Integrate assets into your game engine (Unity, Godot, etc.)")
    print("2. Implement expression switching in dialogue systems")
    print("3. Set up animation transitions between expressions")
    print("4. Test asset loading and performance")
    print("5. Create additional character variants if needed")


if __name__ == "__main__":
    main()