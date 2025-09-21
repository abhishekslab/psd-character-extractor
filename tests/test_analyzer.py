"""
Tests for PSD Analyzer module
"""

import unittest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.psd_extractor.analyzer import PSDAnalyzer


class TestPSDAnalyzer(unittest.TestCase):
    """Test cases for PSDAnalyzer class"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_psd_path = "test_character.psd"

    @patch('src.psd_extractor.analyzer.PSDImage')
    def test_init_loads_psd_successfully(self, mock_psd_image):
        """Test that analyzer initializes and loads PSD file"""
        mock_psd = Mock()
        mock_psd_image.open.return_value = mock_psd

        analyzer = PSDAnalyzer(self.mock_psd_path)

        self.assertEqual(analyzer.psd_path, self.mock_psd_path)
        self.assertEqual(analyzer.psd, mock_psd)
        mock_psd_image.open.assert_called_once_with(self.mock_psd_path)

    @patch('src.psd_extractor.analyzer.PSDImage')
    def test_init_handles_psd_load_error(self, mock_psd_image):
        """Test that analyzer handles PSD load errors properly"""
        mock_psd_image.open.side_effect = Exception("Failed to load PSD")

        with self.assertRaises(Exception) as context:
            PSDAnalyzer(self.mock_psd_path)

        self.assertIn("Failed to load PSD", str(context.exception))

    @patch('src.psd_extractor.analyzer.PSDImage')
    def test_get_basic_info(self, mock_psd_image):
        """Test basic PSD information extraction"""
        mock_psd = Mock()
        mock_psd.width = 1024
        mock_psd.height = 1536
        mock_psd.color_mode = "RGB"
        mock_psd.descendants.return_value = [Mock() for _ in range(25)]
        mock_psd_image.open.return_value = mock_psd

        analyzer = PSDAnalyzer(self.mock_psd_path)
        basic_info = analyzer.get_basic_info()

        expected_info = {
            "width": 1024,
            "height": 1536,
            "color_mode": "RGB",
            "total_layers": 25,
            "file_path": self.mock_psd_path
        }

        self.assertEqual(basic_info, expected_info)

    @patch('src.psd_extractor.analyzer.PSDImage')
    def test_find_expression_layers(self, mock_psd_image):
        """Test expression layer detection"""
        # Create mock layers with expression-related names
        mock_layer1 = Mock()
        mock_layer1.name = "Normal"
        mock_layer1.visible = True

        mock_layer2 = Mock()
        mock_layer2.name = "Smile"
        mock_layer2.visible = False

        mock_layer3 = Mock()
        mock_layer3.name = "Background"
        mock_layer3.visible = True

        mock_psd = Mock()
        mock_psd.descendants.return_value = [mock_layer1, mock_layer2, mock_layer3]
        mock_psd_image.open.return_value = mock_psd

        analyzer = PSDAnalyzer(self.mock_psd_path)
        expressions = analyzer.find_expression_layers()

        # Should find 1 expression layers (Normal and Smile)
        self.assertEqual(len(expressions), 1)
        self.assertEqual(expressions[0]["name"], "Smile")
        self.assertIn("smile", expressions[0]["keywords"])

    @patch('src.psd_extractor.analyzer.PSDImage')
    def test_get_layer_by_name(self, mock_psd_image):
        """Test finding layer by exact name"""
        mock_layer1 = Mock()
        mock_layer1.name = "Normal"

        mock_layer2 = Mock()
        mock_layer2.name = "Smile"

        mock_psd = Mock()
        mock_psd.descendants.return_value = [mock_layer1, mock_layer2]
        mock_psd_image.open.return_value = mock_psd

        analyzer = PSDAnalyzer(self.mock_psd_path)

        # Test finding existing layer
        found_layer = analyzer.get_layer_by_name("Smile")
        self.assertEqual(found_layer, mock_layer2)

        # Test finding non-existing layer
        not_found = analyzer.get_layer_by_name("NonExistent")
        self.assertIsNone(not_found)

    @patch('src.psd_extractor.analyzer.PSDImage')
    def test_get_expression_group(self, mock_psd_image):
        """Test finding expression group layer"""
        mock_expression_group = Mock()
        mock_expression_group.name = "Expression"
        mock_expression_group._layers = [Mock(), Mock()]

        mock_other_layer = Mock()
        mock_other_layer.name = "Background"

        mock_psd = Mock()
        mock_psd.descendants.return_value = [mock_expression_group, mock_other_layer]
        mock_psd_image.open.return_value = mock_psd

        analyzer = PSDAnalyzer(self.mock_psd_path)
        expression_group = analyzer.get_expression_group()

        self.assertEqual(expression_group, mock_expression_group)

    @patch('src.psd_extractor.analyzer.PSDImage')
    def test_list_all_layers(self, mock_psd_image):
        """Test listing all layer names"""
        mock_layer1 = Mock()
        mock_layer1.name = "Layer 1"

        mock_layer2 = Mock()
        mock_layer2.name = "Layer 2"

        mock_layer3 = Mock()
        mock_layer3.name = "   "  # Should be filtered out

        mock_psd = Mock()
        mock_psd.descendants.return_value = [mock_layer1, mock_layer2, mock_layer3]
        mock_psd_image.open.return_value = mock_psd

        analyzer = PSDAnalyzer(self.mock_psd_path)
        layer_names = analyzer.list_all_layers()

        expected_names = ["Layer 1", "Layer 2"]
        self.assertEqual(layer_names, expected_names)

    @patch('src.psd_extractor.analyzer.PSDImage')
    def test_analyze_layer_structure(self, mock_psd_image):
        """Test complete layer structure analysis"""
        mock_layer = Mock()
        mock_layer.name = "Test Layer"
        mock_layer.visible = True
        mock_layer._layers = None  # Not a group

        mock_psd = Mock()
        mock_psd.__iter__ = Mock(return_value=iter([mock_layer]))
        mock_psd_image.open.return_value = mock_psd

        analyzer = PSDAnalyzer(self.mock_psd_path)

        with patch.object(analyzer, 'get_basic_info') as mock_basic_info, \
             patch.object(analyzer, 'find_expression_layers') as mock_find_expr, \
             patch.object(analyzer, '_find_layer_groups') as mock_find_groups:

            mock_basic_info.return_value = {"width": 100, "height": 100}
            mock_find_expr.return_value = []
            mock_find_groups.return_value = {}

            analysis = analyzer.analyze_layer_structure()

            self.assertIn("basic_info", analysis)
            self.assertIn("layer_tree", analysis)
            self.assertIn("expression_analysis", analysis)
            self.assertIn("layer_groups", analysis)

    def test_analyze_layer_without_psd(self):
        """Test that methods raise error when PSD is not loaded"""
        with patch('src.psd_extractor.analyzer.PSDImage') as mock_psd_image:
            mock_psd_image.open.side_effect = Exception("Load failed")

            with self.assertRaises(Exception):
                analyzer = PSDAnalyzer(self.mock_psd_path)


class TestPSDAnalyzerIntegration(unittest.TestCase):
    """Integration tests for PSDAnalyzer with more realistic scenarios"""

    @patch('src.psd_extractor.analyzer.PSDImage')
    def test_realistic_expression_detection(self, mock_psd_image):
        """Test expression detection with realistic layer structure"""
        # Create realistic layer structure
        layers = []

        # Expression layers
        expr_names = ["Normal", "Smile", "Shocked", "Sad", "Happy", "Annoyed"]
        for name in expr_names:
            layer = Mock()
            layer.name = name
            layer.visible = True
            layers.append(layer)

        # Non-expression layers
        other_names = ["Hair", "Body", "Background", "Accessories"]
        for name in other_names:
            layer = Mock()
            layer.name = name
            layer.visible = True
            layers.append(layer)

        mock_psd = Mock()
        mock_psd.descendants.return_value = layers
        mock_psd_image.open.return_value = mock_psd

        analyzer = PSDAnalyzer("test.psd")
        expressions = analyzer.find_expression_layers()

        # Should detect expression layers based on keywords
        expression_names = [expr["name"] for expr in expressions]

        # Check that known expression names are detected
        self.assertIn("Smile", expression_names)
        self.assertIn("Shocked", expression_names)
        self.assertIn("Happy", expression_names)

        # Check that non-expression names are not detected
        self.assertNotIn("Background", expression_names)


if __name__ == '__main__':
    unittest.main()