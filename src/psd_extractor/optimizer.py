"""
Image Optimizer

Optimizes extracted character images for web applications and VTuber systems.
"""

import logging
from typing import Tuple, Optional
from PIL import Image

logger = logging.getLogger(__name__)


class ImageOptimizer:
    """Optimizes images for web and VTuber applications."""

    def __init__(self,
                 target_width: int = 400,
                 target_height: int = 600,
                 quality: int = 85,
                 format_type: str = "PNG"):
        """
        Initialize the image optimizer.

        Args:
            target_width: Target width for optimization
            target_height: Target height for optimization
            quality: Compression quality (1-100)
            format_type: Output format (PNG, JPEG, WEBP)
        """
        self.target_width = target_width
        self.target_height = target_height
        self.quality = quality
        self.format_type = format_type.upper()

    def set_target_size(self, width: int, height: int) -> None:
        """
        Set target dimensions for optimization.

        Args:
            width: Target width in pixels
            height: Target height in pixels
        """
        self.target_width = width
        self.target_height = height
        logger.info(f"Updated target size to {width}x{height}")

    def set_quality(self, quality: int) -> None:
        """
        Set compression quality.

        Args:
            quality: Quality level (1-100, higher is better)
        """
        if not 1 <= quality <= 100:
            raise ValueError("Quality must be between 1 and 100")

        self.quality = quality
        logger.info(f"Updated quality to {quality}")

    def calculate_scaled_size(self, image: Image.Image) -> Tuple[int, int]:
        """
        Calculate scaled dimensions maintaining aspect ratio.

        Args:
            image: PIL Image to calculate scaling for

        Returns:
            Tuple of (width, height) for scaled image
        """
        original_width, original_height = image.size
        original_ratio = original_width / original_height
        target_ratio = self.target_width / self.target_height

        if original_ratio > target_ratio:
            # Image is wider relative to target
            new_width = self.target_width
            new_height = int(self.target_width / original_ratio)
        else:
            # Image is taller relative to target
            new_height = self.target_height
            new_width = int(self.target_height * original_ratio)

        return new_width, new_height

    def resize_image(self, image: Image.Image, size: Optional[Tuple[int, int]] = None) -> Image.Image:
        """
        Resize image with high-quality resampling.

        Args:
            image: PIL Image to resize
            size: Optional specific size, otherwise uses calculated scaled size

        Returns:
            Resized PIL Image
        """
        if size is None:
            size = self.calculate_scaled_size(image)

        try:
            # Use LANCZOS for high-quality resampling
            resized_image = image.resize(size, Image.Resampling.LANCZOS)
            logger.debug(f"Resized image from {image.size} to {size}")
            return resized_image
        except Exception as e:
            logger.error(f"Failed to resize image: {e}")
            return image

    def optimize_for_web(self, image: Image.Image) -> Image.Image:
        """
        Optimize image for web applications.

        Args:
            image: PIL Image to optimize

        Returns:
            Optimized PIL Image
        """
        try:
            # Convert to RGB if necessary (for JPEG output)
            if image.mode == 'RGBA' and self.format_type == 'JPEG':
                # Create white background for JPEG
                background = Image.new('RGB', image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[-1])  # Use alpha channel as mask
                image = background
            elif image.mode != 'RGBA' and self.format_type == 'PNG':
                # Convert to RGBA for PNG with transparency
                image = image.convert('RGBA')

            # Resize image
            optimized_image = self.resize_image(image)

            logger.info(f"Optimized image: {image.size} -> {optimized_image.size}")
            return optimized_image

        except Exception as e:
            logger.error(f"Failed to optimize image: {e}")
            return image

    def optimize_for_vtuber(self, image: Image.Image) -> Image.Image:
        """
        Optimize image specifically for VTuber applications.

        Args:
            image: PIL Image to optimize

        Returns:
            VTuber-optimized PIL Image
        """
        # VTuber-specific optimizations
        vtuber_width = 400
        vtuber_height = 600

        # Temporarily adjust target size
        original_width = self.target_width
        original_height = self.target_height

        self.target_width = vtuber_width
        self.target_height = vtuber_height

        try:
            optimized_image = self.optimize_for_web(image)
            logger.info("Applied VTuber-specific optimizations")
            return optimized_image
        finally:
            # Restore original target size
            self.target_width = original_width
            self.target_height = original_height

    def create_sprite_sheet(self, images: dict, columns: int = 4) -> Image.Image:
        """
        Create a sprite sheet from multiple character expressions.

        Args:
            images: Dictionary of expression name -> PIL Image
            columns: Number of columns in the sprite sheet

        Returns:
            PIL Image containing sprite sheet
        """
        if not images:
            raise ValueError("No images provided for sprite sheet")

        # Get dimensions from first image (assuming all are same size)
        first_image = next(iter(images.values()))
        img_width, img_height = first_image.size

        # Calculate sprite sheet dimensions
        num_images = len(images)
        rows = (num_images + columns - 1) // columns  # Ceiling division

        sheet_width = columns * img_width
        sheet_height = rows * img_height

        # Create sprite sheet
        sprite_sheet = Image.new('RGBA', (sheet_width, sheet_height), (0, 0, 0, 0))

        # Place images in grid
        for i, (name, image) in enumerate(images.items()):
            row = i // columns
            col = i % columns

            x = col * img_width
            y = row * img_height

            sprite_sheet.paste(image, (x, y))

        logger.info(f"Created sprite sheet: {sheet_width}x{sheet_height} with {num_images} expressions")
        return sprite_sheet

    def batch_optimize(self, images: dict, optimization_type: str = "web") -> dict:
        """
        Batch optimize multiple images.

        Args:
            images: Dictionary of name -> PIL Image
            optimization_type: Type of optimization ("web", "vtuber")

        Returns:
            Dictionary of optimized images
        """
        optimized_images = {}

        optimization_func = (
            self.optimize_for_vtuber if optimization_type == "vtuber"
            else self.optimize_for_web
        )

        for name, image in images.items():
            try:
                optimized_images[name] = optimization_func(image)
                logger.debug(f"Optimized image: {name}")
            except Exception as e:
                logger.error(f"Failed to optimize {name}: {e}")
                optimized_images[name] = image  # Use original if optimization fails

        logger.info(f"Batch optimized {len(optimized_images)} images ({optimization_type})")
        return optimized_images

    def get_optimization_settings(self) -> dict:
        """
        Get current optimization settings.

        Returns:
            Dictionary containing current settings
        """
        return {
            "target_width": self.target_width,
            "target_height": self.target_height,
            "quality": self.quality,
            "format": self.format_type
        }