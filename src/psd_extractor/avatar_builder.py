"""
Avatar Bundle Builder

Builds complete avatar bundles with image atlas generation and JSON output.
"""

import json
import logging
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image
from psd_tools import PSDImage

from .auto_mapper import AutoMapper
from .models.avatar import AvatarBundle, AvatarImages, AvatarMeta, SliceRect
from .models.pcs import LayerInfo
from .pcs_scanner import PCSScanner

logger = logging.getLogger(__name__)


class AvatarBuilder:
    """Builds complete avatar bundles from PSD files."""

    def __init__(
        self, psd_path: str, output_dir: str, rules_file: Optional[str] = None
    ):
        """
        Initialize the avatar builder.

        Args:
            psd_path: Path to the PSD file
            output_dir: Output directory for generated files
            rules_file: Optional path to mapping rules file
        """
        self.psd_path = psd_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.scanner = PCSScanner(psd_path)
        self.mapper = AutoMapper(rules_file)
        self.psd: Optional[PSDImage] = None

        self._load_psd()

    def _load_psd(self) -> None:
        """Load the PSD file."""
        try:
            self.psd = PSDImage.open(self.psd_path)
            logger.info(f"Loaded PSD for avatar building: {self.psd_path}")
        except Exception as e:
            logger.error(f"Failed to load PSD file: {e}")
            raise

    def build_avatar(self, avatar_name: Optional[str] = None) -> AvatarBundle:
        """
        Build complete avatar bundle from PSD.

        Args:
            avatar_name: Optional name for the avatar

        Returns:
            Complete AvatarBundle object
        """
        # Scan layers
        layers = self.scanner.scan_layers()
        logger.info(f"Scanned {len(layers)} layers")

        # Map to avatar structure
        avatar = self.mapper.map_layers(layers)

        # Set metadata
        if not avatar_name:
            avatar_name = Path(self.psd_path).stem

        avatar.meta = AvatarMeta(
            name=avatar_name,
            source=Path(self.psd_path).name,
            generator="psd-character-extractor@1.0.0",
        )

        # Extract images and build atlas
        atlas_data = self._extract_and_pack_images(layers, avatar)
        avatar.images = atlas_data

        return avatar

    def _extract_and_pack_images(
        self, layers: List[LayerInfo], avatar: AvatarBundle
    ) -> AvatarImages:
        """
        Extract layer images and pack them into an atlas.

        Args:
            layers: List of layer information
            avatar: Avatar bundle to update

        Returns:
            AvatarImages object with atlas and slice data
        """
        # Extract images for mapped layers
        extracted_images = self._extract_layer_images(layers)

        if not extracted_images:
            logger.warning("No images extracted from layers")
            return AvatarImages(atlas="atlas.png")

        # Pack into atlas
        atlas_image, slice_rects = self._pack_atlas(extracted_images)

        # Save atlas
        atlas_path = self.output_dir / "atlas.png"
        atlas_image.save(atlas_path)
        logger.info(f"Saved atlas: {atlas_path}")

        # Create AvatarImages object
        avatar_images = AvatarImages(atlas="atlas.png", slices=slice_rects)

        return avatar_images

    def _extract_layer_images(self, layers: List[LayerInfo]) -> Dict[str, Image.Image]:
        """
        Extract images from PSD layers.

        Args:
            layers: List of layer information

        Returns:
            Dictionary mapping layer keys to PIL Images
        """
        extracted_images = {}

        if not self.psd:
            return extracted_images

        for layer in layers:
            if not layer.pcs_tag:
                continue

            try:
                # Find the corresponding PSD layer
                psd_layer = self._find_psd_layer(layer.name)
                if not psd_layer:
                    continue

                # Extract layer image
                layer_image = self._extract_single_layer(psd_layer, layer)
                if layer_image:
                    # Generate a key for this layer
                    layer_key = self._generate_layer_key(layer)
                    extracted_images[layer_key] = layer_image
                    logger.debug(f"Extracted image for layer: {layer_key}")

            except Exception as e:
                logger.error(f"Failed to extract image for layer '{layer.name}': {e}")

        logger.info(f"Extracted {len(extracted_images)} layer images")
        return extracted_images

    def _find_psd_layer(self, layer_name: str):
        """Find a PSD layer by name."""
        if not self.psd:
            return None

        # Simple recursive search for the layer
        def search_recursive(container, target_name):
            if hasattr(container, "__iter__"):
                for layer in container:
                    if layer.name == target_name:
                        return layer
                    result = search_recursive(layer, target_name)
                    if result:
                        return result
            return None

        return search_recursive(self.psd, layer_name)

    def _extract_single_layer(
        self, psd_layer, layer_info: LayerInfo
    ) -> Optional[Image.Image]:
        """
        Extract a single layer as PIL Image.

        Args:
            psd_layer: PSD layer object
            layer_info: Layer information

        Returns:
            PIL Image or None if extraction fails
        """
        try:
            # Make layer temporarily visible and hide others
            original_visibility = psd_layer.visible

            # Enable the target layer
            psd_layer.visible = True

            # Get the composite image with only this layer visible
            # Note: This is a simplified approach. For production use, you'd want
            # to properly isolate layers by manipulating visibility of all layers
            composite_image = psd_layer.composite()

            if composite_image:
                # Convert to PIL Image
                return composite_image

        except Exception as e:
            logger.error(f"Failed to extract layer image: {e}")
        finally:
            # Restore original visibility
            try:
                psd_layer.visible = original_visibility
            except:
                pass

        return None

    def _generate_layer_key(self, layer: LayerInfo) -> str:
        """
        Generate a unique key for a layer based on its PCS tag.

        Args:
            layer: Layer information

        Returns:
            Unique layer key
        """
        if not layer.pcs_tag:
            return f"Unknown/{layer.name}"

        parts = []

        if layer.pcs_tag.group:
            parts.append(layer.pcs_tag.group)

        if layer.pcs_tag.part:
            parts.append(layer.pcs_tag.part)
            if layer.pcs_tag.side:
                parts.append(f"[{layer.pcs_tag.side}]")

        state_key = layer.pcs_tag.to_state_key()
        if state_key != "default":
            parts.append(state_key)

        return "/".join(parts) if parts else layer.name

    def _pack_atlas(
        self, images: Dict[str, Image.Image]
    ) -> Tuple[Image.Image, Dict[str, SliceRect]]:
        """
        Pack multiple images into a single atlas.

        Args:
            images: Dictionary mapping keys to PIL Images

        Returns:
            Tuple of (atlas_image, slice_rectangles)
        """
        if not images:
            # Return empty atlas
            empty_atlas = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
            return empty_atlas, {}

        # Sort images by area (largest first) for better packing
        sorted_items = sorted(
            images.items(), key=lambda x: x[1].size[0] * x[1].size[1], reverse=True
        )

        # Simple bin packing algorithm
        atlas_width, atlas_height, slice_rects = self._simple_bin_pack(sorted_items)

        # Create atlas image
        atlas = Image.new("RGBA", (atlas_width, atlas_height), (0, 0, 0, 0))

        # Paste images into atlas
        for key, image in images.items():
            if key in slice_rects:
                rect = slice_rects[key]
                atlas.paste(image, (rect.x, rect.y), image)

        logger.info(
            f"Created atlas: {atlas_width}x{atlas_height} with {len(slice_rects)} slices"
        )
        return atlas, slice_rects

    def _simple_bin_pack(
        self, sorted_items: List[Tuple[str, Image.Image]]
    ) -> Tuple[int, int, Dict[str, SliceRect]]:
        """
        Simple bin packing algorithm for atlas generation.

        Args:
            sorted_items: List of (key, image) tuples sorted by size

        Returns:
            Tuple of (width, height, slice_rectangles)
        """
        if not sorted_items:
            return 1, 1, {}

        # Calculate total area and estimate atlas size
        total_area = sum(img.size[0] * img.size[1] for _, img in sorted_items)
        atlas_size = max(512, int(math.sqrt(total_area) * 1.2))  # Add 20% padding

        # Simple shelf-packing algorithm
        slice_rects = {}
        current_x = 0
        current_y = 0
        row_height = 0
        atlas_width = atlas_size
        atlas_height = atlas_size

        for key, image in sorted_items:
            img_width, img_height = image.size

            # Check if image fits in current row
            if current_x + img_width > atlas_width:
                # Move to next row
                current_x = 0
                current_y += row_height
                row_height = 0

            # Check if we need to expand atlas height
            if current_y + img_height > atlas_height:
                atlas_height = max(atlas_height * 2, current_y + img_height)

            # Place image
            slice_rects[key] = SliceRect(
                x=current_x, y=current_y, w=img_width, h=img_height
            )

            # Update position
            current_x += img_width
            row_height = max(row_height, img_height)

        # Final atlas dimensions
        actual_width = (
            max(rect.x + rect.w for rect in slice_rects.values())
            if slice_rects
            else atlas_size
        )
        actual_height = (
            max(rect.y + rect.h for rect in slice_rects.values())
            if slice_rects
            else atlas_size
        )

        return actual_width, actual_height, slice_rects

    def save_avatar_bundle(
        self, avatar: AvatarBundle, filename: str = "avatar.json"
    ) -> str:
        """
        Save avatar bundle to JSON file.

        Args:
            avatar: Avatar bundle to save
            filename: Output filename

        Returns:
            Path to saved file
        """
        output_path = self.output_dir / filename

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(avatar.to_dict(), f, indent=2, ensure_ascii=False)

        logger.info(f"Saved avatar bundle: {output_path}")
        return str(output_path)

    def generate_report(
        self, layers: List[LayerInfo], avatar: AvatarBundle, filename: str = "report.md"
    ) -> str:
        """
        Generate mapping report.

        Args:
            layers: Original layer list
            avatar: Generated avatar bundle
            filename: Output filename

        Returns:
            Path to saved report
        """
        report = self.mapper.generate_mapping_report(layers, avatar)
        output_path = self.output_dir / filename

        # Generate markdown report
        md_content = self._generate_markdown_report(report, avatar)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        logger.info(f"Saved mapping report: {output_path}")
        return str(output_path)

    def _generate_markdown_report(
        self, report: Dict[str, Any], avatar: AvatarBundle
    ) -> str:
        """Generate markdown content for the mapping report."""
        md_lines = [
            "# Avatar Mapping Report",
            "",
            "## Summary",
            f"- Total layers: {report['summary']['total_layers']}",
            f"- Mapped layers: {report['summary']['mapped_layers']}",
            f"- Unmapped layers: {report['summary']['unmapped_layers']}",
            f"- Slots created: {report['summary']['slots_created']}",
            "",
        ]

        if report["warnings"]:
            md_lines.extend(["## Warnings", ""])
            for warning in report["warnings"]:
                md_lines.append(f"- ⚠️ {warning}")
            md_lines.append("")

        md_lines.extend(["## Slot Coverage", ""])

        for slot_name, slot_def in avatar.slots.items():
            md_lines.append(f"### {slot_name}")
            if slot_def.states:
                md_lines.append(f"- States: {', '.join(slot_def.states)}")
            if slot_def.visemes:
                md_lines.append(f"- Visemes: {', '.join(slot_def.visemes)}")
            if slot_def.emotions:
                md_lines.append(f"- Emotions: {', '.join(slot_def.emotions)}")
            if slot_def.shapes:
                md_lines.append(f"- Shapes: {', '.join(slot_def.shapes)}")
            md_lines.append("")

        if report["unmapped_layers"]:
            md_lines.extend(["## Unmapped Layers", ""])
            for layer_name in report["unmapped_layers"]:
                md_lines.append(f"- {layer_name}")

        return "\n".join(md_lines)
