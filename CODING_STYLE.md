# Coding Style Guide

This document outlines the coding conventions, naming patterns, and architectural principles used in the PSD Character Extractor project.

## Project Structure

The project follows a clean, modular architecture with clear separation of concerns:

```
src/psd_extractor/
├── __init__.py          # Public API exports
├── extractor.py         # Main extraction engine
├── analyzer.py          # PSD structure analysis
├── optimizer.py         # Image optimization
├── batch.py             # Batch processing
└── cli.py               # Command-line interface
```

## Naming Conventions

### Classes
- **PascalCase** for class names
- Descriptive, domain-specific names
- Examples: `CharacterExtractor`, `PSDAnalyzer`, `ImageOptimizer`, `BatchProcessor`

### Functions and Methods
- **snake_case** for all function and method names
- Verb-based names for actions
- Examples: `extract_expression()`, `analyze_layer_structure()`, `optimize_for_web()`

### Variables
- **snake_case** for variable names
- Descriptive names avoiding abbreviations
- Examples: `expression_mapping`, `target_width`, `psd_path`

### Constants
- **UPPER_CASE** with underscores
- Class-level constants for default configurations
- Examples: `DEFAULT_EXPRESSION_MAPPING`, `MAX_WORKERS`

### Files and Modules
- **snake_case** for module names
- Single-word descriptive names when possible
- Examples: `extractor.py`, `analyzer.py`, `optimizer.py`

## Clean Architecture Patterns

### 1. Single Responsibility Principle
Each class has a focused, well-defined purpose:

- **CharacterExtractor**: Coordinates expression extraction workflow
- **PSDAnalyzer**: Analyzes PSD file structure and identifies layers
- **ImageOptimizer**: Handles image optimization and format conversion
- **BatchProcessor**: Manages concurrent processing of multiple files

### 2. Dependency Injection
Classes accept dependencies through constructor parameters:

```python
class CharacterExtractor:
    def __init__(self, psd_path: str, expression_mapping: Optional[Dict] = None):
        self.analyzer = PSDAnalyzer(psd_path)
        self.optimizer = ImageOptimizer()
```

### 3. Strategy Pattern
Different optimization strategies for various use cases:

```python
def optimize_for_web(self, image: Image.Image) -> Image.Image
def optimize_for_vtuber(self, image: Image.Image) -> Image.Image
```

### 4. Factory Pattern
Implicit factory pattern for creating extractors with different configurations:

```python
# Different configurations for different use cases
extractor = CharacterExtractor(psd_path, custom_mapping)
```

### 5. Command Pattern
CLI commands are structured as separate command functions:

```python
@cli.command()
def extract(psd_file: str, output: str, ...):
    """Extract character expressions from PSD file."""

@cli.command()
def analyze(psd_file: str, detailed: bool, ...):
    """Analyze PSD file structure."""
```

### 6. Observer Pattern
Progress tracking in batch operations using tqdm:

```python
for future in tqdm(as_completed(future_to_file),
                   total=len(future_to_file),
                   desc="Extracting characters"):
```

## Code Organization Principles

### 1. Module Structure
Each module follows consistent organization:

```python
"""
Module docstring explaining purpose
"""

# Standard library imports
import logging
import os
from typing import Dict, List, Optional

# Third-party imports
from psd_tools import PSDImage
from PIL import Image

# Local imports
from .analyzer import PSDAnalyzer

# Module-level constants
logger = logging.getLogger(__name__)

# Classes and functions
```

### 2. Class Structure
Classes follow a consistent internal organization:

```python
class ClassName:
    """Class docstring with purpose and usage."""

    # Class constants
    DEFAULT_SETTING = value

    def __init__(self, ...):
        """Initialize with required parameters."""

    # Public methods
    def public_method(self):
        """Public interface methods."""

    # Private methods
    def _private_method(self):
        """Internal implementation methods."""
```

### 3. Method Organization
- Public interface methods first
- Private/internal methods prefixed with underscore
- Helper methods grouped logically

### 4. Error Handling
Consistent error handling patterns:

```python
try:
    # Main logic
    result = operation()
    logger.info(f"Success: {result}")
    return result
except Exception as e:
    logger.error(f"Operation failed: {e}")
    return None  # or raise
```

## Documentation Standards

### 1. Docstrings
All classes and functions have comprehensive docstrings:

```python
def extract_expression(self, expression_name: str) -> Optional[any]:
    """
    Extract a single expression from the PSD.

    Args:
        expression_name: Name of the expression layer to extract

    Returns:
        PIL Image of the extracted expression, or None if extraction fails
    """
```

### 2. Type Hints
Comprehensive type hints throughout the codebase:

```python
def analyze_layer_structure(self) -> Dict[str, any]:
def find_psd_files(self, directory: Optional[str] = None) -> List[Path]:
def process_directory(self, input_dir: str, output_dir: str) -> Dict[str, Dict]:
```

### 3. Logging
Structured logging with appropriate levels:

```python
logger.info(f"Loaded PSD file: {self.psd_path}")
logger.warning(f"Expression '{expression_name}' not found")
logger.error(f"Failed to extract expression: {e}")
logger.debug(f"Resized image from {image.size} to {size}")
```

## Configuration Management

### 1. Default Configurations
Class-level constants for default settings:

```python
DEFAULT_EXPRESSION_MAPPING = {
    'closed': ['normal', 'neutral', 'smug'],
    'small': ['smile', 'smile 2', 'happy'],
    'medium': ['delighted', 'annoyed', 'excited'],
    'wide': ['shocked', 'laugh', 'surprised']
}
```

### 2. Configurable Parameters
Constructor parameters for customization:

```python
def __init__(self,
             target_width: int = 400,
             target_height: int = 600,
             quality: int = 85,
             format_type: str = "PNG"):
```

### 3. External Configuration
JSON files for complex configurations:

```python
with open(mapping_file, 'r', encoding='utf-8') as f:
    self.expression_mapping = json.load(f)
```

## Testing Patterns

### 1. Test Organization
Tests mirror source structure:

```
tests/
├── test_extractor.py
├── test_analyzer.py
├── test_optimizer.py
└── test_cli.py
```

### 2. Mock Usage
Extensive use of mocks for external dependencies:

```python
@patch('src.psd_extractor.extractor.PSDImage')
@patch('src.psd_extractor.extractor.PSDAnalyzer')
def test_init_with_default_mapping(self, mock_analyzer, mock_psd_image):
```

### 3. Test Categories
Tests organized by type using pytest markers:

```python
@pytest.mark.unit
@pytest.mark.integration
@pytest.mark.cli
@pytest.mark.slow
```

## Performance Considerations

### 1. Concurrent Processing
ThreadPoolExecutor for batch operations:

```python
with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
    future_to_file = {
        executor.submit(self._extract_single_file, str(psd_file), mapping): psd_file
        for psd_file in psd_files
    }
```

### 2. Resource Management
Context managers and proper cleanup:

```python
try:
    # Enable the target expression
    target_expression.visible = True
    composite_image = self.psd.composite()
    return composite_image
finally:
    # Restore original visibility
    target_expression.visible = original_visibility
```

### 3. Memory Efficiency
Avoid loading multiple large files simultaneously in batch processing.

## CLI Design Principles

### 1. Command Structure
Separate commands for different workflows:

- `psd-extract`: Extract expressions from single PSD
- `psd-analyze`: Analyze PSD structure
- `psd-batch`: Batch process multiple files
- `psd-list-expressions`: List available expressions
- `psd-create-mapping`: Create mapping template

### 2. User Experience
- Colored output for success/error/warning messages
- Progress bars for long operations
- Verbose and quiet modes
- Comprehensive help text

### 3. Output Formatting
Consistent output formatting with visual indicators:

```python
def print_success(message: str) -> None:
    click.echo(f"{Fore.GREEN}✓ {message}{Style.RESET_ALL}")

def print_error(message: str) -> None:
    click.echo(f"{Fore.RED}✗ {message}{Style.RESET_ALL}")
```

## Development Tools Integration

### 1. Code Formatting
- **Black** with 88-character line length
- **isort** with black-compatible profile
- Configured in `pyproject.toml`

### 2. Type Checking
- **mypy** for static type checking
- Gradual typing approach (not strictly required)
- External library stubs ignored

### 3. Linting
- **flake8** with black-compatible settings
- Excludes E203, E501, W503 for black compatibility
- Per-file ignores for specific cases

### 4. Testing
- **pytest** with coverage reporting
- 70% minimum coverage requirement
- Multiple test markers for different test types

This coding style guide ensures consistency, maintainability, and scalability across the PSD Character Extractor codebase while following modern Python development best practices.