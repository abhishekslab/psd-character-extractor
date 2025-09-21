"""
Tests for Character Extractor module
"""

import unittest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.psd_extractor.extractor import CharacterExtractor


class TestCharacterExtractor(unittest.TestCase):
    """Test cases for CharacterExtractor class"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_psd_path = "test_character.psd"

    @patch('src.psd_extractor.extractor.PSDAnalyzer')
    @patch('src.psd_extractor.extractor.PSDImage')
    def test_init_with_default_mapping(self, mock_psd_image, mock_analyzer):
        """Test extractor initialization with default expression mapping"""
        mock_psd = Mock()
        mock_psd_image.open.return_value = mock_psd

        extractor = CharacterExtractor(self.mock_psd_path)

        self.assertEqual(extractor.psd_path, self.mock_psd_path)
        self.assertEqual(extractor.psd, mock_psd)
        self.assertEqual(extractor.expression_mapping, CharacterExtractor.DEFAULT_EXPRESSION_MAPPING)

    @patch('src.psd_extractor.extractor.PSDAnalyzer')
    @patch('src.psd_extractor.extractor.PSDImage')
    def test_init_with_custom_mapping(self, mock_psd_image, mock_analyzer):
        """Test extractor initialization with custom expression mapping"""
        custom_mapping = {
            'happy': ['joy', 'smile'],
            'sad': ['crying', 'melancholy']
        }

        mock_psd = Mock()
        mock_psd_image.open.return_value = mock_psd

        extractor = CharacterExtractor(self.mock_psd_path, custom_mapping)

        self.assertEqual(extractor.expression_mapping, custom_mapping)

    @patch('src.psd_extractor.extractor.PSDAnalyzer')
    @patch('src.psd_extractor.extractor.PSDImage')
    def test_set_expression_mapping(self, mock_psd_image, mock_analyzer):
        """Test updating expression mapping"""
        mock_psd = Mock()
        mock_psd_image.open.return_value = mock_psd

        extractor = CharacterExtractor(self.mock_psd_path)

        new_mapping = {'test': ['layer1', 'layer2']}
        extractor.set_expression_mapping(new_mapping)

        self.assertEqual(extractor.expression_mapping, new_mapping)

    @patch('src.psd_extractor.extractor.PSDAnalyzer')
    @patch('src.psd_extractor.extractor.PSDImage')
    def test_get_available_expressions(self, mock_psd_image, mock_analyzer):
        """Test getting available expression layer names"""
        mock_psd = Mock()
        mock_psd_image.open.return_value = mock_psd

        mock_analyzer_instance = mock_analyzer.return_value
        mock_analyzer_instance.find_expression_layers.return_value = [
            {"name": "Smile", "keywords": ["smile"]},
            {"name": "Sad", "keywords": ["sad"]},
            {"name": "Normal", "keywords": ["normal"]}
        ]

        extractor = CharacterExtractor(self.mock_psd_path)
        expressions = extractor.get_available_expressions()

        expected = ["Smile", "Sad", "Normal"]
        self.assertEqual(expressions, expected)

    @patch('src.psd_extractor.extractor.PSDAnalyzer')
    @patch('src.psd_extractor.extractor.PSDImage')
    def test_extract_expression_success(self, mock_psd_image, mock_analyzer):
        """Test successful single expression extraction"""
        mock_psd = Mock()
        mock_composite_image = Mock()
        mock_psd.composite.return_value = mock_composite_image
        mock_psd_image.open.return_value = mock_psd

        # Mock analyzer methods
        mock_analyzer_instance = mock_analyzer.return_value
        mock_expression_group = Mock()
        mock_expression_group._layers = []
        mock_analyzer_instance.get_expression_group.return_value = mock_expression_group

        mock_target_layer = Mock()
        mock_target_layer.visible = False
        mock_analyzer_instance.get_layer_by_name.return_value = mock_target_layer

        extractor = CharacterExtractor(self.mock_psd_path)
        result = extractor.extract_expression("Smile")

        self.assertEqual(result, mock_composite_image)
        # Verify layer visibility was managed
        self.assertTrue(mock_target_layer.visible)

    @patch('src.psd_extractor.extractor.PSDAnalyzer')
    @patch('src.psd_extractor.extractor.PSDImage')
    def test_extract_expression_layer_not_found(self, mock_psd_image, mock_analyzer):
        """Test expression extraction when layer is not found"""
        mock_psd = Mock()
        mock_psd_image.open.return_value = mock_psd

        mock_analyzer_instance = mock_analyzer.return_value
        mock_expression_group = Mock()
        mock_analyzer_instance.get_expression_group.return_value = mock_expression_group
        mock_analyzer_instance.get_layer_by_name.return_value = None  # Layer not found

        extractor = CharacterExtractor(self.mock_psd_path)
        result = extractor.extract_expression("NonExistent")

        self.assertIsNone(result)

    @patch('src.psd_extractor.extractor.PSDAnalyzer')
    @patch('src.psd_extractor.extractor.PSDImage')
    def test_extract_expressions_with_mapping(self, mock_psd_image, mock_analyzer):
        """Test extracting multiple expressions using mapping"""
        mock_psd = Mock()
        mock_psd_image.open.return_value = mock_psd

        # Setup mock for successful extraction
        mock_analyzer_instance = mock_analyzer.return_value
        mock_expression_group = Mock()
        mock_expression_group._layers = []
        mock_analyzer_instance.get_expression_group.return_value = mock_expression_group

        mock_layer = Mock()
        mock_layer.visible = False
        mock_analyzer_instance.get_layer_by_name.return_value = mock_layer

        mock_image = Mock()
        mock_psd.composite.return_value = mock_image

        extractor = CharacterExtractor(self.mock_psd_path)

        # Override mapping for predictable test
        extractor.expression_mapping = {
            'closed': ['normal'],
            'small': ['smile']
        }

        expressions = extractor.extract_expressions()

        # Should extract both states
        self.assertIn('closed', expressions)
        self.assertIn('small', expressions)
        self.assertEqual(expressions['closed'], mock_image)
        self.assertEqual(expressions['small'], mock_image)

    @patch('src.psd_extractor.extractor.PSDAnalyzer')
    @patch('src.psd_extractor.extractor.PSDImage')
    def test_extract_expressions_selective(self, mock_psd_image, mock_analyzer):
        """Test extracting only specific expression states"""
        mock_psd = Mock()
        mock_psd_image.open.return_value = mock_psd

        # Setup successful extraction mock
        mock_analyzer_instance = mock_analyzer.return_value
        mock_expression_group = Mock()
        mock_expression_group._layers = []
        mock_analyzer_instance.get_expression_group.return_value = mock_expression_group

        mock_layer = Mock()
        mock_layer.visible = False
        mock_analyzer_instance.get_layer_by_name.return_value = mock_layer

        mock_image = Mock()
        mock_psd.composite.return_value = mock_image

        extractor = CharacterExtractor(self.mock_psd_path)
        extractor.expression_mapping = {
            'closed': ['normal'],
            'small': ['smile'],
            'wide': ['shocked']
        }

        # Extract only specific states
        expressions = extractor.extract_expressions(target_states=['closed', 'small'])

        # Should only extract requested states
        self.assertIn('closed', expressions)
        self.assertIn('small', expressions)
        self.assertNotIn('wide', expressions)
        self.assertEqual(len(expressions), 2)

    @patch('src.psd_extractor.extractor.PSDAnalyzer')
    @patch('src.psd_extractor.extractor.PSDImage')
    def test_save_expressions(self, mock_psd_image, mock_analyzer):
        """Test saving expressions to files"""
        mock_psd = Mock()
        mock_psd_image.open.return_value = mock_psd

        extractor = CharacterExtractor(self.mock_psd_path)

        # Create mock expressions
        mock_image1 = Mock()
        mock_image2 = Mock()
        expressions = {
            'closed': mock_image1,
            'small': mock_image2
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock the optimizer
            with patch.object(extractor.optimizer, 'optimize_for_web') as mock_optimize:
                mock_optimize.side_effect = lambda x: x  # Return input unchanged

                saved_files = extractor.save_expressions(
                    expressions,
                    temp_dir,
                    optimize=True,
                    prefix="test"
                )

                # Check that files were "saved"
                self.assertIn('closed', saved_files)
                self.assertIn('small', saved_files)

                # Check file paths
                expected_closed = str(Path(temp_dir) / "test-closed.png")
                expected_small = str(Path(temp_dir) / "test-small.png")

                self.assertEqual(saved_files['closed'], expected_closed)
                self.assertEqual(saved_files['small'], expected_small)

                # Verify images were saved
                mock_image1.save.assert_called_once_with(expected_closed, "PNG")
                mock_image2.save.assert_called_once_with(expected_small, "PNG")

    @patch('src.psd_extractor.extractor.PSDAnalyzer')
    @patch('src.psd_extractor.extractor.PSDImage')
    def test_get_extraction_summary(self, mock_psd_image, mock_analyzer):
        """Test getting extraction summary"""
        mock_psd = Mock()
        mock_psd_image.open.return_value = mock_psd

        mock_analyzer_instance = mock_analyzer.return_value
        mock_analyzer_instance.get_basic_info.return_value = {
            "width": 100,
            "height": 100
        }
        mock_analyzer_instance.find_expression_layers.return_value = [
            {"name": "normal", "keywords": ["normal"]},
            {"name": "smile", "keywords": ["smile"]}
        ]

        extractor = CharacterExtractor(self.mock_psd_path)
        extractor.expression_mapping = {
            'closed': ['normal'],
            'small': ['smile'],
            'wide': ['shocked']  # This won't be found
        }

        summary = extractor.get_extraction_summary()

        self.assertIn("psd_info", summary)
        self.assertIn("available_expressions", summary)
        self.assertIn("mappable_lip_sync_states", summary)
        self.assertIn("total_extractable", summary)

        # Should find mappable states for available expressions
        mappable = summary["mappable_lip_sync_states"]
        self.assertIn('closed', mappable)  # normal is available
        self.assertIn('small', mappable)   # smile is available
        self.assertNotIn('wide', mappable)  # shocked is not available

        self.assertEqual(summary["total_extractable"], 2)


class TestCharacterExtractorErrorHandling(unittest.TestCase):
    """Test error handling in CharacterExtractor"""

    @patch('src.psd_extractor.extractor.PSDImage')
    def test_psd_load_failure(self, mock_psd_image):
        """Test handling PSD load failures"""
        mock_psd_image.open.side_effect = Exception("Cannot open PSD file")

        with self.assertRaises(Exception):
            CharacterExtractor("invalid.psd")

    @patch('src.psd_extractor.extractor.PSDAnalyzer')
    @patch('src.psd_extractor.extractor.PSDImage')
    def test_extract_expression_with_exception(self, mock_psd_image, mock_analyzer):
        """Test expression extraction handles exceptions gracefully"""
        mock_psd = Mock()
        mock_psd.composite.side_effect = Exception("Composite failed")
        mock_psd_image.open.return_value = mock_psd

        mock_analyzer_instance = mock_analyzer.return_value
        mock_expression_group = Mock()
        mock_analyzer_instance.get_expression_group.return_value = mock_expression_group
        mock_analyzer_instance.get_layer_by_name.return_value = Mock()

        extractor = CharacterExtractor("test.psd")
        result = extractor.extract_expression("test")

        # Should return None when extraction fails
        self.assertIsNone(result)

    @patch('src.psd_extractor.extractor.PSDAnalyzer')
    @patch('src.psd_extractor.extractor.PSDImage')
    def test_save_expressions_with_none_images(self, mock_psd_image, mock_analyzer):
        """Test saving expressions handles None images gracefully"""
        mock_psd = Mock()
        mock_psd_image.open.return_value = mock_psd

        extractor = CharacterExtractor("test.psd")

        expressions = {
            'valid': Mock(),
            'invalid': None  # This should be skipped
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            saved_files = extractor.save_expressions(expressions, temp_dir)

            # Should only save valid expressions
            self.assertIn('valid', saved_files)
            self.assertNotIn('invalid', saved_files)
            self.assertEqual(len(saved_files), 1)


if __name__ == '__main__':
    unittest.main()