# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PSD Character Extractor is a Python library for automated character extraction from Photoshop PSD files, specifically designed for VTuber applications, game development, and animation workflows. The tool analyzes PSD layer structures, extracts character expressions, and maps them to lip sync states for animation systems.

## Development Commands

### Setup and Installation
```bash
# Install for development
pip install -e ".[dev]"

# Install all dependencies including test and docs
pip install -e ".[all]"
```

### Testing
```bash
# Run all tests with coverage
pytest tests/ -v --cov=src/psd_extractor --cov-report=term-missing

# Run tests with coverage and HTML report
pytest tests/ -v --cov=src/psd_extractor --cov-report=html

# Run specific test types
pytest tests/ -m unit          # Unit tests only
pytest tests/ -m integration   # Integration tests only
pytest tests/ -m cli           # CLI tests only

# Run tests excluding slow tests
pytest tests/ -m "not slow"
```

### Code Quality and Linting
```bash
# Format code with black
black src/ tests/

# Check code formatting
black --check --diff src/ tests/

# Sort imports with isort
isort src/ tests/

# Check import sorting
isort --check-only --diff src/ tests/

# Lint with flake8
flake8 src/ tests/ --max-line-length=88

# Type checking with mypy
mypy src/ --ignore-missing-imports
```

### Building and Distribution
```bash
# Build package
python -m build

# Check package build
twine check dist/*

# Install package locally from build
pip install dist/*.whl
```

### CLI Commands for Testing
```bash
# Extract expressions from PSD
psd-extract character.psd --output ./output

# Analyze PSD structure
psd-analyze character.psd --verbose

# Batch process multiple PSDs
psd-batch --input ./psds --output ./extracted

# Create expression mapping template
psd-create-mapping --output expressions.json

# List available expressions in PSD
psd-list-expressions character.psd
```

### Web Application
```bash
# Start web interface for interactive PSD processing
python -c "
from src.psd_extractor.web_api import app
import uvicorn
uvicorn.run(app, host='0.0.0.0', port=8001)
"

# Alternative: Start with custom host/port
python -c "
from src.psd_extractor.web_api import app
import uvicorn
uvicorn.run(app, host='localhost', port=8000)
"
```

## Architecture Overview

### Core Components

1. **CharacterExtractor** (`src/psd_extractor/extractor.py`): Main extraction engine
   - Loads PSD files and extracts character expressions
   - Maps expressions to lip sync states (closed, small, medium, wide)
   - Coordinates with analyzer and optimizer components

2. **PSDAnalyzer** (`src/psd_extractor/analyzer.py`): PSD structure analysis
   - Parses PSD layer hierarchy and metadata
   - Identifies potential expression layers
   - Provides layer organization insights

3. **ImageOptimizer** (`src/psd_extractor/optimizer.py`): Output optimization
   - Handles image compression and format conversion
   - Optimizes for web applications and real-time usage
   - Configurable quality and size settings

4. **BatchProcessor** (`src/psd_extractor/batch.py`): Bulk processing
   - Processes multiple PSD files concurrently
   - Supports custom expression mappings via JSON files
   - Thread-based parallel processing with progress tracking

5. **CLI Interface** (`src/psd_extractor/cli.py`): Command-line tools
   - Multiple CLI commands for different workflows
   - Colorized output using colorama
   - Progress bars and verbose logging options

### Expression Mapping System

The core workflow revolves around mapping PSD layer names to lip sync animation states:

```python
DEFAULT_EXPRESSION_MAPPING = {
    'closed': ['normal', 'neutral', 'smug'],
    'small': ['smile', 'smile 2', 'happy'],
    'medium': ['delighted', 'annoyed', 'excited'],
    'wide': ['shocked', 'laugh', 'surprised']
}
```

This mapping allows VTuber software and game engines to automatically select appropriate character expressions based on voice input or dialogue requirements.

### Dependencies

Core dependencies:
- `psd-tools>=1.10.0`: PSD file parsing and layer extraction
- `Pillow>=10.0.0`: Image processing and format conversion
- `click>=8.0.0`: CLI framework
- `tqdm>=4.64.0`: Progress bars for batch operations
- `colorama>=0.4.4`: Cross-platform colored terminal output

### Configuration Files

- `pyproject.toml`: Primary configuration for build system, dependencies, and all development tools
- `setup.py`: Legacy setup script for backward compatibility
- `requirements.txt`: Minimal production dependencies
- `.github/workflows/ci.yml`: Comprehensive CI/CD pipeline with multi-platform testing

### Testing Strategy

- **Unit tests**: Core functionality testing in `tests/test_*.py`
- **Integration tests**: End-to-end workflow testing
- **CLI tests**: Command-line interface validation
- **Performance tests**: Benchmarking for optimization workflows
- Coverage target: 70% minimum (configured in pyproject.toml)

### Development Workflow

1. Code changes should follow the black formatting standard (88 character line length)
2. Import sorting follows the black-compatible isort profile
3. Type hints are encouraged but not strictly required
4. All new features should include corresponding tests
5. CLI commands should provide both verbose and quiet output modes
6. Expression mappings should be configurable via JSON files

### Key Design Patterns

- **Factory pattern**: For creating extractors with different configurations
- **Strategy pattern**: For different optimization strategies
- **Observer pattern**: For progress tracking in batch operations
- **Command pattern**: For CLI command structure

### Performance Considerations

- Batch processing uses ThreadPoolExecutor for concurrent PSD file processing
- Image optimization settings can be tuned for different use cases (web vs. high-quality)
- PSD files are loaded once and reused for multiple expression extractions
- Progress tracking uses tqdm for user feedback during long operations

This architecture supports the primary use cases of VTuber avatar creation, game character asset generation, and animation workflow automation while maintaining extensibility for custom expression mapping systems.