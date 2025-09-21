#!/usr/bin/env python3
"""
VTuber Integration Examples

This script demonstrates how to integrate PSD Character Extractor
with VTuber applications and real-time streaming setups.
"""

import json
import time
import logging
from pathlib import Path
from typing import Dict, List

from psd_extractor import CharacterExtractor, ImageOptimizer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VTuberCharacterSetup:
    """
    Helper class for setting up VTuber character assets
    """

    def __init__(self, psd_file: str, output_dir: str = "./vtuber_assets"):
        self.psd_file = psd_file
        self.output_dir = Path(output_dir)
        self.extractor = CharacterExtractor(psd_file)

        # VTuber-specific optimization settings
        self.optimizer = ImageOptimizer(
            target_width=400,   # Standard VTuber size
            target_height=600,
            quality=90,         # High quality for streaming
            format_type="PNG"   # PNG for transparency
        )

    def create_standard_lipSync_set(self) -> Dict[str, str]:
        """
        Create the standard 4-state lip sync set for VTuber applications.

        Returns:
            Dictionary mapping lip sync states to file paths
        """
        logger.info("Creating standard VTuber lip sync set...")

        # Extract the 4 standard lip sync states
        expressions = self.extractor.extract_expressions()

        if len(expressions) < 4:
            logger.warning(f"Only extracted {len(expressions)} expressions, expected 4")

        # Save with VTuber-optimized settings
        self.output_dir.mkdir(parents=True, exist_ok=True)

        saved_files = {}
        for state, image in expressions.items():
            if image is not None:
                # Apply VTuber optimization
                optimized_image = self.optimizer.optimize_for_vtuber(image)

                # Save with descriptive filename
                filename = f"vtuber_{state}.png"
                file_path = self.output_dir / filename

                optimized_image.save(str(file_path), "PNG")
                saved_files[state] = str(file_path)

                logger.info(f"Saved VTuber asset: {filename}")

        return saved_files

    def create_sprite_sheet(self) -> str:
        """
        Create a sprite sheet for applications that prefer single-file assets.

        Returns:
            Path to the generated sprite sheet
        """
        logger.info("Creating VTuber sprite sheet...")

        expressions = self.extractor.extract_expressions()

        if not expressions:
            raise ValueError("No expressions extracted for sprite sheet")

        # Optimize all images first
        optimized_expressions = {}
        for state, image in expressions.items():
            if image is not None:
                optimized_expressions[state] = self.optimizer.optimize_for_vtuber(image)

        # Create sprite sheet (2x2 grid)
        sprite_sheet = self.optimizer.create_sprite_sheet(optimized_expressions, columns=2)

        # Save sprite sheet
        sprite_path = self.output_dir / "vtuber_sprite_sheet.png"
        sprite_sheet.save(str(sprite_path), "PNG")

        logger.info(f"Sprite sheet saved: {sprite_path}")
        return str(sprite_path)

    def generate_config_file(self, saved_files: Dict[str, str]) -> str:
        """
        Generate a configuration file for VTuber applications.

        Args:
            saved_files: Dictionary of lip sync state to file path

        Returns:
            Path to the generated config file
        """
        config = {
            "character_name": Path(self.psd_file).stem,
            "lip_sync_assets": saved_files,
            "settings": {
                "image_format": "PNG",
                "has_transparency": True,
                "recommended_size": {
                    "width": 400,
                    "height": 600
                },
                "lip_sync_states": {
                    "closed": "Use during silence or consonants",
                    "small": "Use for quiet speech or 'ee' sounds",
                    "medium": "Use for normal speech or 'ah' sounds",
                    "wide": "Use for loud speech or 'oh' sounds"
                }
            },
            "generated_by": "PSD Character Extractor",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        config_path = self.output_dir / "vtuber_config.json"
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

        logger.info(f"VTuber config saved: {config_path}")
        return str(config_path)


def example_obs_integration():
    """
    Example: Prepare assets for OBS Studio integration

    Many VTubers use OBS Studio for streaming. This example shows
    how to prepare assets in the right format for OBS.
    """
    print("=== OBS Studio Integration Example ===")

    psd_file = "character.psd"  # Replace with your PSD file

    try:
        # Setup for OBS streaming
        vtuber_setup = VTuberCharacterSetup(psd_file, "./obs_assets")

        # Create standard lip sync set
        lip_sync_files = vtuber_setup.create_standard_lipSync_set()

        # Generate OBS-specific config
        config_path = vtuber_setup.generate_config_file(lip_sync_files)

        print("OBS Assets created:")
        for state, file_path in lip_sync_files.items():
            print(f"  {state}: {file_path}")

        print(f"\nOBS Configuration: {config_path}")
        print("\nOBS Setup Instructions:")
        print("1. Add 'Image Source' for each lip sync state")
        print("2. Use hotkeys or third-party tools to switch between states")
        print("3. Set up audio-reactive switching with tools like VTube Studio")

    except Exception as e:
        print(f"Error: {e}")


def example_vtube_studio_prep():
    """
    Example: Prepare assets for VTube Studio

    VTube Studio is a popular VTubing application that supports
    live2D-style animations with PNG sequences.
    """
    print("\n=== VTube Studio Preparation Example ===")

    psd_file = "character.psd"

    try:
        # Setup with VTube Studio specific settings
        setup = VTuberCharacterSetup(psd_file, "./vtube_studio_assets")

        # VTube Studio prefers specific naming conventions
        extractor = setup.extractor

        # Create custom mapping for VTube Studio
        vtube_mapping = {
            'mouth_closed': ['normal', 'neutral', 'smug'],
            'mouth_small': ['smile', 'happy'],
            'mouth_medium': ['delighted', 'talking'],
            'mouth_large': ['shocked', 'laugh', 'wide']
        }

        # Set custom mapping
        extractor.set_expression_mapping(vtube_mapping)

        # Extract with custom mapping
        expressions = extractor.extract_expressions()

        # Save with VTube Studio naming
        output_dir = setup.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        saved_files = {}
        for state, image in expressions.items():
            if image is not None:
                # VTube Studio optimization
                optimized = setup.optimizer.optimize_for_vtuber(image)

                # VTube Studio filename format
                filename = f"character_{state}.png"
                file_path = output_dir / filename

                optimized.save(str(file_path), "PNG")
                saved_files[state] = str(file_path)

        print("VTube Studio assets created:")
        for state, file_path in saved_files.items():
            print(f"  {state}: {file_path}")

        # Create VTube Studio import guide
        guide_path = output_dir / "vtube_studio_guide.txt"
        with open(guide_path, 'w') as f:
            f.write("VTube Studio Import Guide\n")
            f.write("=" * 30 + "\n\n")
            f.write("1. Open VTube Studio\n")
            f.write("2. Go to Settings > Model Settings\n")
            f.write("3. Import each PNG file as a separate expression\n")
            f.write("4. Set up lip sync mapping:\n")
            for state, file_path in saved_files.items():
                filename = Path(file_path).name
                f.write(f"   - {state}: {filename}\n")
            f.write("\n5. Configure audio-reactive lip sync in VTube Studio settings\n")

        print(f"\nSetup guide created: {guide_path}")

    except Exception as e:
        print(f"Error: {e}")


def example_streaming_workflow():
    """
    Example: Complete streaming workflow setup

    This example shows a complete workflow for setting up
    VTuber assets for various streaming platforms.
    """
    print("\n=== Complete Streaming Workflow Example ===")

    psd_file = "character.psd"

    try:
        # Create multiple asset sets for different use cases
        base_dir = "./streaming_assets"

        # 1. High-quality assets for close-up shots
        hq_setup = VTuberCharacterSetup(psd_file, f"{base_dir}/high_quality")
        hq_setup.optimizer.set_target_size(800, 1200)  # Larger size
        hq_setup.optimizer.set_quality(95)  # Higher quality
        hq_files = hq_setup.create_standard_lipSync_set()

        # 2. Standard assets for normal streaming
        std_setup = VTuberCharacterSetup(psd_file, f"{base_dir}/standard")
        std_files = std_setup.create_standard_lipSync_set()

        # 3. Mobile-optimized assets for phone streaming
        mobile_setup = VTuberCharacterSetup(psd_file, f"{base_dir}/mobile")
        mobile_setup.optimizer.set_target_size(200, 300)  # Smaller size
        mobile_setup.optimizer.set_quality(80)  # Lower quality for mobile
        mobile_files = mobile_setup.create_standard_lipSync_set()

        # 4. Create sprite sheets for each quality level
        hq_sprite = hq_setup.create_sprite_sheet()
        std_sprite = std_setup.create_sprite_sheet()
        mobile_sprite = mobile_setup.create_sprite_sheet()

        # 5. Generate comprehensive config
        master_config = {
            "streaming_assets": {
                "high_quality": {
                    "description": "Use for close-up shots or high-end streaming",
                    "files": hq_files,
                    "sprite_sheet": hq_sprite
                },
                "standard": {
                    "description": "Use for normal streaming setup",
                    "files": std_files,
                    "sprite_sheet": std_sprite
                },
                "mobile": {
                    "description": "Use for mobile streaming or low bandwidth",
                    "files": mobile_files,
                    "sprite_sheet": mobile_sprite
                }
            },
            "usage_instructions": {
                "twitch": "Use standard quality for most Twitch streams",
                "youtube": "Use high quality for YouTube recordings",
                "discord": "Use mobile quality for Discord video calls",
                "obs": "Import standard quality files as image sources"
            }
        }

        config_path = Path(base_dir) / "master_config.json"
        with open(config_path, 'w') as f:
            json.dump(master_config, f, indent=2)

        print("Complete streaming asset set created:")
        print(f"  High Quality: {len(hq_files)} files")
        print(f"  Standard: {len(std_files)} files")
        print(f"  Mobile: {len(mobile_files)} files")
        print(f"  Master Config: {config_path}")

    except Exception as e:
        print(f"Error: {e}")


def example_realtime_lipSync_simulation():
    """
    Example: Simulate real-time lip sync switching

    This example shows how you might use the extracted assets
    in a real-time lip sync application.
    """
    print("\n=== Real-time Lip Sync Simulation ===")

    # This is a simulation - in a real application, you'd get
    # audio levels from a microphone or audio processing library

    def simulate_audio_levels():
        """Simulate audio amplitude levels"""
        import random
        return random.uniform(0, 1)

    def audio_to_mouth_state(audio_level: float) -> str:
        """Convert audio level to mouth state"""
        if audio_level < 0.1:
            return 'closed'
        elif audio_level < 0.4:
            return 'small'
        elif audio_level < 0.7:
            return 'medium'
        else:
            return 'wide'

    # Load asset paths (in a real app, these would be loaded once at startup)
    assets_dir = "./vtuber_assets"
    asset_files = {
        'closed': f"{assets_dir}/vtuber_closed.png",
        'small': f"{assets_dir}/vtuber_small.png",
        'medium': f"{assets_dir}/vtuber_medium.png",
        'wide': f"{assets_dir}/vtuber_wide.png"
    }

    print("Simulating real-time lip sync (5 seconds)...")
    print("Audio Level -> Mouth State -> Asset File")
    print("-" * 50)

    # Simulate 5 seconds of real-time switching
    for i in range(25):  # 5 FPS simulation
        audio_level = simulate_audio_levels()
        mouth_state = audio_to_mouth_state(audio_level)
        asset_file = asset_files.get(mouth_state, "unknown")

        print(f"{audio_level:.2f} -> {mouth_state:>6} -> {Path(asset_file).name}")

        time.sleep(0.2)  # 5 FPS

    print("\nReal-time simulation complete!")
    print("\nIntegration notes:")
    print("- Use audio processing libraries like PyAudio for real audio input")
    print("- Implement smoothing to avoid rapid state changes")
    print("- Consider using a game engine like Unity or Godot for rendering")
    print("- Add blinking and idle animations for more lifelike movement")


def main():
    """
    Run all VTuber integration examples
    """
    print("PSD Character Extractor - VTuber Integration Examples")
    print("=" * 60)

    # Note: Make sure you have a PSD file named 'character.psd'
    # or modify the psd_file variable in each example

    example_obs_integration()
    example_vtube_studio_prep()
    example_streaming_workflow()
    example_realtime_lipSync_simulation()

    print("\n" + "=" * 60)
    print("All VTuber examples completed!")
    print("\nNext steps for VTuber integration:")
    print("1. Test assets in your preferred VTubing software")
    print("2. Set up audio-reactive lip sync")
    print("3. Add additional animations (blinking, expressions)")
    print("4. Configure streaming software (OBS, XSplit)")
    print("5. Test with your audience!")


if __name__ == "__main__":
    main()