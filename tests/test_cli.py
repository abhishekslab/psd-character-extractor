"""
Tests for CLI module
"""

import unittest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, call
from click.testing import CliRunner

from src.psd_extractor.cli import cli, analyze, extract, batch, create_mapping, list_expressions


class TestCLI(unittest.TestCase):
    """Test cases for CLI commands"""

    def setUp(self):
        """Set up test fixtures"""
        self.runner = CliRunner()

    def test_cli_help(self):
        """Test that CLI shows help information"""
        result = self.runner.invoke(cli, ['--help'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("PSD Character Extractor", result.output)

    def test_cli_verbose_flag(self):
        """Test verbose flag sets logging level"""
        with patch('src.psd_extractor.cli.logging') as mock_logging:
            mock_logger = Mock()
            mock_logging.getLogger.return_value = mock_logger

            result = self.runner.invoke(cli, ['--verbose', 'analyze', 'test.psd'])

            # Check that debug level was set
            mock_logger.setLevel.assert_called_with(mock_logging.DEBUG)

    def test_cli_quiet_flag(self):
        """Test quiet flag sets logging level"""
        with patch('src.psd_extractor.cli.logging') as mock_logging:
            mock_logger = Mock()
            mock_logging.getLogger.return_value = mock_logger

            result = self.runner.invoke(cli, ['--quiet', 'analyze', 'test.psd'])

            # Check that error level was set
            mock_logger.setLevel.assert_called_with(mock_logging.ERROR)


class TestAnalyzeCommand(unittest.TestCase):
    """Test cases for the analyze command"""

    def setUp(self):
        """Set up test fixtures"""
        self.runner = CliRunner()

    @patch('src.psd_extractor.cli.PSDAnalyzer')
    def test_analyze_basic(self, mock_analyzer_class):
        """Test basic analysis command"""
        mock_analyzer = Mock()
        mock_analyzer_class.return_value = mock_analyzer

        with tempfile.NamedTemporaryFile(suffix='.psd', delete=False) as temp_file:
            result = self.runner.invoke(analyze, [temp_file.name])

            self.assertEqual(result.exit_code, 0)
            mock_analyzer_class.assert_called_once_with(temp_file.name)
            mock_analyzer.print_analysis_report.assert_called_once()

    @patch('src.psd_extractor.cli.PSDAnalyzer')
    def test_analyze_detailed_with_output(self, mock_analyzer_class):
        """Test detailed analysis with JSON output"""
        mock_analyzer = Mock()
        mock_analyzer_class.return_value = mock_analyzer

        mock_analysis = {
            "basic_info": {"width": 100, "height": 100},
            "expression_analysis": [],
            "layer_groups": {}
        }
        mock_analyzer.analyze_layer_structure.return_value = mock_analysis

        with tempfile.NamedTemporaryFile(suffix='.psd', delete=False) as temp_psd, \
             tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_json:

            result = self.runner.invoke(analyze, [
                temp_psd.name,
                '--detailed',
                '--output', temp_json.name
            ])

            self.assertEqual(result.exit_code, 0)
            mock_analyzer.analyze_layer_structure.assert_called_once()

    @patch('src.psd_extractor.cli.PSDAnalyzer')
    def test_analyze_file_not_found(self, mock_analyzer_class):
        """Test analyze command with non-existent file"""
        result = self.runner.invoke(analyze, ['nonexistent.psd'])

        # Should exit with error due to file not found
        self.assertNotEqual(result.exit_code, 0)

    @patch('src.psd_extractor.cli.PSDAnalyzer')
    def test_analyze_exception_handling(self, mock_analyzer_class):
        """Test analyze command handles exceptions"""
        mock_analyzer_class.side_effect = Exception("Analysis failed")

        with tempfile.NamedTemporaryFile(suffix='.psd', delete=False) as temp_file:
            result = self.runner.invoke(analyze, [temp_file.name])

            self.assertEqual(result.exit_code, 1)
            self.assertIn("Analysis failed", result.output)


class TestExtractCommand(unittest.TestCase):
    """Test cases for the extract command"""

    def setUp(self):
        """Set up test fixtures"""
        self.runner = CliRunner()

    @patch('src.psd_extractor.cli.CharacterExtractor')
    def test_extract_basic(self, mock_extractor_class):
        """Test basic extraction command"""
        mock_extractor = Mock()
        mock_extractor_class.return_value = mock_extractor

        mock_summary = {
            'total_extractable': 4
        }
        mock_extractor.get_extraction_summary.return_value = mock_summary

        mock_expressions = {
            'closed': Mock(),
            'small': Mock()
        }
        mock_extractor.extract_expressions.return_value = mock_expressions

        mock_saved_files = {
            'closed': './output/character-closed.png',
            'small': './output/character-small.png'
        }
        mock_extractor.save_expressions.return_value = mock_saved_files

        with tempfile.NamedTemporaryFile(suffix='.psd', delete=False) as temp_file:
            result = self.runner.invoke(extract, [temp_file.name])

            self.assertEqual(result.exit_code, 0)
            mock_extractor_class.assert_called_once_with(temp_file.name, None)
            mock_extractor.extract_expressions.assert_called_once()
            mock_extractor.save_expressions.assert_called_once()

    @patch('src.psd_extractor.cli.CharacterExtractor')
    def test_extract_with_custom_options(self, mock_extractor_class):
        """Test extraction with custom options"""
        mock_extractor = Mock()
        mock_extractor_class.return_value = mock_extractor

        mock_summary = {'total_extractable': 2}
        mock_extractor.get_extraction_summary.return_value = mock_summary

        mock_expressions = {'closed': Mock()}
        mock_extractor.extract_expressions.return_value = mock_expressions

        mock_saved_files = {'closed': './custom/prefix-closed.png'}
        mock_extractor.save_expressions.return_value = mock_saved_files

        with tempfile.NamedTemporaryFile(suffix='.psd', delete=False) as temp_file, \
             tempfile.TemporaryDirectory() as temp_dir:

            result = self.runner.invoke(extract, [
                temp_file.name,
                '--output', temp_dir,
                '--prefix', 'custom',
                '--states', 'closed',
                '--no-optimize',
                '--format', 'jpg'
            ])

            self.assertEqual(result.exit_code, 0)

            # Check that extract was called with specific states
            mock_extractor.extract_expressions.assert_called_once_with(target_states=['closed'])

            # Check that save was called with correct parameters
            mock_extractor.save_expressions.assert_called_once_with(
                mock_expressions,
                temp_dir,
                optimize=False,
                prefix='custom'
            )

    @patch('src.psd_extractor.cli.CharacterExtractor')
    def test_extract_with_mapping_file(self, mock_extractor_class):
        """Test extraction with custom mapping file"""
        mock_extractor = Mock()
        mock_extractor_class.return_value = mock_extractor

        mock_summary = {'total_extractable': 1}
        mock_extractor.get_extraction_summary.return_value = mock_summary

        custom_mapping = {'happy': ['smile', 'joy']}

        with tempfile.NamedTemporaryFile(suffix='.psd', delete=False) as temp_psd, \
             tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_mapping:

            # Write mapping to file
            json.dump(custom_mapping, temp_mapping)
            temp_mapping.flush()

            mock_expressions = {'happy': Mock()}
            mock_extractor.extract_expressions.return_value = mock_expressions
            mock_extractor.save_expressions.return_value = {'happy': 'file.png'}

            result = self.runner.invoke(extract, [
                temp_psd.name,
                '--mapping', temp_mapping.name
            ])

            self.assertEqual(result.exit_code, 0)
            mock_extractor_class.assert_called_once_with(temp_psd.name, custom_mapping)

    @patch('src.psd_extractor.cli.CharacterExtractor')
    def test_extract_no_expressions_found(self, mock_extractor_class):
        """Test extraction when no expressions are found"""
        mock_extractor = Mock()
        mock_extractor_class.return_value = mock_extractor

        mock_summary = {'total_extractable': 0}
        mock_extractor.get_extraction_summary.return_value = mock_summary

        with tempfile.NamedTemporaryFile(suffix='.psd', delete=False) as temp_file:
            result = self.runner.invoke(extract, [temp_file.name])

            self.assertEqual(result.exit_code, 0)
            self.assertIn("No extractable expressions found", result.output)


class TestBatchCommand(unittest.TestCase):
    """Test cases for the batch command"""

    def setUp(self):
        """Set up test fixtures"""
        self.runner = CliRunner()

    @patch('src.psd_extractor.cli.BatchProcessor')
    def test_batch_basic(self, mock_processor_class):
        """Test basic batch processing"""
        mock_processor = Mock()
        mock_processor_class.return_value = mock_processor

        mock_psd_files = [Path('file1.psd'), Path('file2.psd')]
        mock_processor.find_psd_files.return_value = mock_psd_files

        mock_results = {
            'file1.psd': {'success': True},
            'file2.psd': {'success': True}
        }
        mock_processor.extract_batch.return_value = mock_results

        with tempfile.TemporaryDirectory() as input_dir, \
             tempfile.TemporaryDirectory() as output_dir:

            result = self.runner.invoke(batch, [
                input_dir,
                '--output', output_dir
            ])

            self.assertEqual(result.exit_code, 0)
            mock_processor_class.assert_called_once_with(
                input_dir=input_dir,
                output_dir=output_dir,
                mapping_file=None,
                max_workers=4
            )

    @patch('src.psd_extractor.cli.BatchProcessor')
    def test_batch_with_report(self, mock_processor_class):
        """Test batch processing with report generation"""
        mock_processor = Mock()
        mock_processor_class.return_value = mock_processor

        mock_processor.find_psd_files.return_value = [Path('test.psd')]
        mock_processor.extract_batch.return_value = {'test.psd': {'success': True}}

        with tempfile.TemporaryDirectory() as input_dir, \
             tempfile.TemporaryDirectory() as output_dir:

            result = self.runner.invoke(batch, [
                input_dir,
                '--output', output_dir,
                '--workers', '8',
                '--report'
            ])

            self.assertEqual(result.exit_code, 0)

            # Check that report was generated
            mock_processor.generate_batch_report.assert_called_once()

    @patch('src.psd_extractor.cli.BatchProcessor')
    def test_batch_no_files_found(self, mock_processor_class):
        """Test batch processing when no PSD files are found"""
        mock_processor = Mock()
        mock_processor_class.return_value = mock_processor

        mock_processor.find_psd_files.return_value = []

        with tempfile.TemporaryDirectory() as input_dir, \
             tempfile.TemporaryDirectory() as output_dir:

            result = self.runner.invoke(batch, [
                input_dir,
                '--output', output_dir
            ])

            self.assertEqual(result.exit_code, 0)
            self.assertIn("No PSD files found", result.output)


class TestCreateMappingCommand(unittest.TestCase):
    """Test cases for the create-mapping command"""

    def setUp(self):
        """Set up test fixtures"""
        self.runner = CliRunner()

    def test_create_mapping_default(self):
        """Test creating mapping template with default filename"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('src.psd_extractor.cli.os.getcwd', return_value=temp_dir):
                result = self.runner.invoke(create_mapping)

                self.assertEqual(result.exit_code, 0)
                self.assertIn("Expression mapping template created", result.output)

                # Check that file was created
                mapping_file = Path(temp_dir) / "expression_mapping.json"
                self.assertTrue(mapping_file.exists())

                # Check file content
                with open(mapping_file) as f:
                    mapping_data = json.load(f)

                self.assertIn("closed", mapping_data)
                self.assertIn("small", mapping_data)
                self.assertIn("medium", mapping_data)
                self.assertIn("wide", mapping_data)

    def test_create_mapping_custom_output(self):
        """Test creating mapping template with custom filename"""
        with tempfile.TemporaryDirectory() as temp_dir:
            custom_file = Path(temp_dir) / "custom_mapping.json"

            result = self.runner.invoke(create_mapping, [
                '--output', str(custom_file)
            ])

            self.assertEqual(result.exit_code, 0)
            self.assertTrue(custom_file.exists())


class TestListExpressionsCommand(unittest.TestCase):
    """Test cases for the list-expressions command"""

    def setUp(self):
        """Set up test fixtures"""
        self.runner = CliRunner()

    @patch('src.psd_extractor.cli.CharacterExtractor')
    def test_list_expressions_basic(self, mock_extractor_class):
        """Test basic expression listing"""
        mock_extractor = Mock()
        mock_extractor_class.return_value = mock_extractor

        mock_expressions = ['Normal', 'Smile', 'Shocked']
        mock_extractor.get_available_expressions.return_value = mock_expressions

        mock_summary = {
            'mappable_lip_sync_states': {
                'closed': ['Normal'],
                'small': ['Smile']
            }
        }
        mock_extractor.get_extraction_summary.return_value = mock_summary

        with tempfile.NamedTemporaryFile(suffix='.psd', delete=False) as temp_file:
            result = self.runner.invoke(list_expressions, [temp_file.name])

            self.assertEqual(result.exit_code, 0)
            self.assertIn("Available Expressions (3)", result.output)
            self.assertIn("Normal", result.output)
            self.assertIn("Smile", result.output)
            self.assertIn("Shocked", result.output)

    @patch('src.psd_extractor.cli.CharacterExtractor')
    def test_list_expressions_none_found(self, mock_extractor_class):
        """Test expression listing when no expressions are found"""
        mock_extractor = Mock()
        mock_extractor_class.return_value = mock_extractor

        mock_extractor.get_available_expressions.return_value = []

        with tempfile.NamedTemporaryFile(suffix='.psd', delete=False) as temp_file:
            result = self.runner.invoke(list_expressions, [temp_file.name])

            self.assertEqual(result.exit_code, 0)
            self.assertIn("No expression layers found", result.output)


class TestCLIIntegration(unittest.TestCase):
    """Integration tests for CLI commands"""

    def setUp(self):
        """Set up test fixtures"""
        self.runner = CliRunner()

    def test_command_chaining_workflow(self):
        """Test a realistic workflow using multiple commands"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # First create a mapping template
            mapping_file = Path(temp_dir) / "test_mapping.json"
            result1 = self.runner.invoke(create_mapping, [
                '--output', str(mapping_file)
            ])
            self.assertEqual(result1.exit_code, 0)

            # Verify mapping file was created and has correct structure
            self.assertTrue(mapping_file.exists())
            with open(mapping_file) as f:
                mapping_data = json.load(f)
            self.assertIn("closed", mapping_data)


if __name__ == '__main__':
    unittest.main()