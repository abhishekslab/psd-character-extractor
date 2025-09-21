"""
Tests for Image Optimizer module
"""

import unittest
from unittest.mock import Mock, patch
from PIL import Image

from src.psd_extractor.optimizer import ImageOptimizer


class TestImageOptimizer(unittest.TestCase):
    """Test cases for ImageOptimizer class"""

    def setUp(self):
        """Set up test fixtures"""
        self.optimizer = ImageOptimizer(
            target_width=400,
            target_height=600,
            quality=85,
            format_type="PNG"
        )

    def test_init_with_defaults(self):
        """Test optimizer initialization with default values"""
        optimizer = ImageOptimizer()

        self.assertEqual(optimizer.target_width, 400)
        self.assertEqual(optimizer.target_height, 600)
        self.assertEqual(optimizer.quality, 85)
        self.assertEqual(optimizer.format_type, "PNG")

    def test_init_with_custom_values(self):
        """Test optimizer initialization with custom values"""
        optimizer = ImageOptimizer(
            target_width=800,
            target_height=1200,
            quality=95,
            format_type="JPEG"
        )

        self.assertEqual(optimizer.target_width, 800)
        self.assertEqual(optimizer.target_height, 1200)
        self.assertEqual(optimizer.quality, 95)
        self.assertEqual(optimizer.format_type, "JPEG")

    def test_set_target_size(self):
        """Test setting target dimensions"""
        self.optimizer.set_target_size(800, 1200)

        self.assertEqual(self.optimizer.target_width, 800)
        self.assertEqual(self.optimizer.target_height, 1200)

    def test_set_quality_valid(self):
        """Test setting valid quality value"""
        self.optimizer.set_quality(95)
        self.assertEqual(self.optimizer.quality, 95)

    def test_set_quality_invalid_low(self):
        """Test setting quality below valid range"""
        with self.assertRaises(ValueError) as context:
            self.optimizer.set_quality(0)
        self.assertIn("Quality must be between 1 and 100", str(context.exception))

    def test_set_quality_invalid_high(self):
        """Test setting quality above valid range"""
        with self.assertRaises(ValueError) as context:
            self.optimizer.set_quality(101)
        self.assertIn("Quality must be between 1 and 100", str(context.exception))

    def test_calculate_scaled_size_wider_image(self):
        """Test scaling calculation for wider images"""
        # Mock image that's wider than target ratio
        mock_image = Mock()
        mock_image.size = (800, 400)  # 2:1 ratio (wider)

        # Target is 400:600 (2:3 ratio)
        scaled_size = self.optimizer.calculate_scaled_size(mock_image)

        # Should scale to target width
        self.assertEqual(scaled_size[0], 400)  # Target width
        self.assertEqual(scaled_size[1], 200)  # Calculated height

    def test_calculate_scaled_size_taller_image(self):
        """Test scaling calculation for taller images"""
        # Mock image that's taller than target ratio
        mock_image = Mock()
        mock_image.size = (300, 900)  # 1:3 ratio (taller)

        # Target is 400:600 (2:3 ratio)
        scaled_size = self.optimizer.calculate_scaled_size(mock_image)

        # Should scale to target height
        self.assertEqual(scaled_size[0], 200)  # Calculated width
        self.assertEqual(scaled_size[1], 600)  # Target height

    @patch('src.psd_extractor.optimizer.Image')
    def test_resize_image_success(self, mock_image_class):
        """Test successful image resizing"""
        # Create mock input image
        mock_input_image = Mock()
        mock_input_image.size = (800, 600)

        # Create mock resized image
        mock_resized_image = Mock()
        mock_input_image.resize.return_value = mock_resized_image

        result = self.optimizer.resize_image(mock_input_image, (400, 300))

        # Check that resize was called with correct parameters
        mock_input_image.resize.assert_called_once_with((400, 300), mock_image_class.Resampling.LANCZOS)
        self.assertEqual(result, mock_resized_image)

    @patch('src.psd_extractor.optimizer.Image')
    def test_resize_image_with_exception(self, mock_image_class):
        """Test image resizing handles exceptions"""
        # Create mock input image that fails to resize
        mock_input_image = Mock()
        mock_input_image.resize.side_effect = Exception("Resize failed")

        result = self.optimizer.resize_image(mock_input_image, (400, 300))

        # Should return original image on failure
        self.assertEqual(result, mock_input_image)

    @patch('src.psd_extractor.optimizer.Image')
    def test_optimize_for_web_rgba_to_jpeg(self, mock_image_class):
        """Test web optimization converting RGBA to JPEG"""
        # Create mock RGBA image
        mock_input_image = Mock()
        mock_input_image.mode = 'RGBA'
        mock_input_image.size = (800, 600)
        mock_input_image.split.return_value = [Mock(), Mock(), Mock(), Mock()]  # R, G, B, A

        # Create mock background image
        mock_background = Mock()
        mock_image_class.new.return_value = mock_background

        # Setup optimizer for JPEG output
        self.optimizer.format_type = "JPEG"

        # Mock resize method
        with patch.object(self.optimizer, 'resize_image') as mock_resize:
            mock_resize.return_value = mock_background

            result = self.optimizer.optimize_for_web(mock_input_image)

            # Verify background was created and pasted
            mock_image_class.new.assert_called_once_with('RGB', (800, 600), (255, 255, 255))
            mock_background.paste.assert_called_once()
            mock_resize.assert_called_once_with(mock_background)

    @patch('src.psd_extractor.optimizer.Image')
    def test_optimize_for_web_rgb_to_png(self, mock_image_class):
        """Test web optimization converting RGB to PNG"""
        # Create mock RGB image
        mock_input_image = Mock()
        mock_input_image.mode = 'RGB'
        mock_converted_image = Mock()
        mock_input_image.convert.return_value = mock_converted_image

        # Setup optimizer for PNG output
        self.optimizer.format_type = "PNG"

        # Mock resize method
        with patch.object(self.optimizer, 'resize_image') as mock_resize:
            mock_resize.return_value = mock_converted_image

            result = self.optimizer.optimize_for_web(mock_input_image)

            # Verify conversion to RGBA for PNG
            mock_input_image.convert.assert_called_once_with('RGBA')
            mock_resize.assert_called_once_with(mock_converted_image)

    def test_optimize_for_vtuber(self):
        """Test VTuber-specific optimization"""
        mock_image = Mock()

        with patch.object(self.optimizer, 'optimize_for_web') as mock_optimize_web:
            mock_optimized = Mock()
            mock_optimize_web.return_value = mock_optimized

            # Store original target size
            original_width = self.optimizer.target_width
            original_height = self.optimizer.target_height

            result = self.optimizer.optimize_for_vtuber(mock_image)

            # Should temporarily change to VTuber dimensions
            mock_optimize_web.assert_called_once_with(mock_image)

            # Should restore original dimensions
            self.assertEqual(self.optimizer.target_width, original_width)
            self.assertEqual(self.optimizer.target_height, original_height)

            self.assertEqual(result, mock_optimized)

    @patch('src.psd_extractor.optimizer.Image')
    def test_create_sprite_sheet(self, mock_image_class):
        """Test sprite sheet creation"""
        # Create mock images
        mock_image1 = Mock()
        mock_image1.size = (100, 150)

        mock_image2 = Mock()
        mock_image2.size = (100, 150)

        mock_image3 = Mock()
        mock_image3.size = (100, 150)

        images = {
            'expression1': mock_image1,
            'expression2': mock_image2,
            'expression3': mock_image3
        }

        # Create mock sprite sheet
        mock_sprite_sheet = Mock()
        mock_image_class.new.return_value = mock_sprite_sheet

        result = self.optimizer.create_sprite_sheet(images, columns=2)

        # Check sprite sheet creation
        # With 3 images and 2 columns, should be 2x2 grid (400x300)
        mock_image_class.new.assert_called_once_with('RGBA', (200, 300), (0, 0, 0, 0))

        # Check that images were pasted
        self.assertEqual(mock_sprite_sheet.paste.call_count, 3)

        self.assertEqual(result, mock_sprite_sheet)

    def test_create_sprite_sheet_empty(self):
        """Test sprite sheet creation with empty input"""
        with self.assertRaises(ValueError) as context:
            self.optimizer.create_sprite_sheet({})
        self.assertIn("No images provided", str(context.exception))

    def test_batch_optimize_web(self):
        """Test batch optimization for web"""
        mock_image1 = Mock()
        mock_image2 = Mock()

        images = {
            'image1': mock_image1,
            'image2': mock_image2
        }

        with patch.object(self.optimizer, 'optimize_for_web') as mock_optimize:
            mock_optimize.side_effect = lambda x: x  # Return input unchanged

            result = self.optimizer.batch_optimize(images, "web")

            # Check that all images were optimized
            self.assertEqual(len(result), 2)
            self.assertEqual(mock_optimize.call_count, 2)
            self.assertIn('image1', result)
            self.assertIn('image2', result)

    def test_batch_optimize_vtuber(self):
        """Test batch optimization for VTuber"""
        mock_image = Mock()
        images = {'image1': mock_image}

        with patch.object(self.optimizer, 'optimize_for_vtuber') as mock_optimize:
            mock_optimize.return_value = mock_image

            result = self.optimizer.batch_optimize(images, "vtuber")

            mock_optimize.assert_called_once_with(mock_image)
            self.assertEqual(result['image1'], mock_image)

    def test_batch_optimize_with_error(self):
        """Test batch optimization handles errors gracefully"""
        mock_image1 = Mock()
        mock_image2 = Mock()

        images = {
            'good_image': mock_image1,
            'bad_image': mock_image2
        }

        def mock_optimize(image):
            if image == mock_image2:
                raise Exception("Optimization failed")
            return image

        with patch.object(self.optimizer, 'optimize_for_web', side_effect=mock_optimize):
            result = self.optimizer.batch_optimize(images, "web")

            # Should include both images (original returned for failed one)
            self.assertEqual(len(result), 2)
            self.assertEqual(result['good_image'], mock_image1)
            self.assertEqual(result['bad_image'], mock_image2)  # Original returned

    def test_get_optimization_settings(self):
        """Test getting current optimization settings"""
        settings = self.optimizer.get_optimization_settings()

        expected_settings = {
            "target_width": 400,
            "target_height": 600,
            "quality": 85,
            "format": "PNG"
        }

        self.assertEqual(settings, expected_settings)


class TestImageOptimizerIntegration(unittest.TestCase):
    """Integration tests for ImageOptimizer with realistic scenarios"""

    def test_realistic_optimization_workflow(self):
        """Test a realistic optimization workflow"""
        optimizer = ImageOptimizer(
            target_width=400,
            target_height=600,
            quality=90,
            format_type="PNG"
        )

        # Test the complete workflow with mocked PIL operations
        with patch('src.psd_extractor.optimizer.Image') as mock_image_class:
            mock_input_image = Mock()
            mock_input_image.mode = 'RGBA'
            mock_input_image.size = (800, 1200)

            mock_resized = Mock()
            mock_input_image.resize.return_value = mock_resized

            with patch.object(optimizer, 'calculate_scaled_size') as mock_calc:
                mock_calc.return_value = (400, 600)

                result = optimizer.optimize_for_web(mock_input_image)

                # Verify the workflow
                mock_calc.assert_called_once_with(mock_input_image)
                mock_input_image.resize.assert_called_once_with((400, 600), mock_image_class.Resampling.LANCZOS)


if __name__ == '__main__':
    unittest.main()