# PSD Character Extractor Documentation

Welcome to the comprehensive documentation for PSD Character Extractor - a powerful Python library for extracting character expressions from Photoshop PSD files for VTuber applications, games, and interactive media.

## Table of Contents

- [Quick Start Guide](quick-start.md)
- [Installation](installation.md)
- [CLI Reference](cli-reference.md)
- [Python API Reference](api-reference.md)
- [Expression Mapping Guide](expression-mapping.md)
- [Batch Processing](batch-processing.md)
- [Image Optimization](optimization.md)
- [Troubleshooting](troubleshooting.md)
- [Contributing](../CONTRIBUTING.md)

## What is PSD Character Extractor?

PSD Character Extractor is a specialized tool designed to analyze and extract character expressions from layered Photoshop (PSD/PSB) files. It's particularly useful for:

- **VTuber Applications**: Extract lip sync expressions for real-time streaming
- **Game Development**: Generate character assets for dialogue systems
- **Animation Projects**: Extract expressions for 2D character animation
- **Interactive Media**: Create expression sets for chatbots and virtual assistants

## Key Features

### 🔍 **Intelligent Analysis**
- Automatically detects expression layers using keyword matching
- Analyzes PSD structure and layer organization
- Identifies potential lip sync states and mappings

### 🎭 **Expression Extraction**
- Maps expressions to standard lip sync states (closed, small, medium, wide)
- Supports custom expression mapping via JSON configuration
- Extracts full character composites with selected expressions

### 🚀 **Batch Processing**
- Process multiple PSD files simultaneously
- Multi-threaded extraction for improved performance
- Comprehensive progress tracking and error reporting

### 🎨 **Image Optimization**
- Web-optimized output with configurable quality settings
- VTuber-specific optimization presets
- Multiple output formats (PNG, JPEG, WebP)
- Automatic resizing with aspect ratio preservation

### 💻 **CLI & Python API**
- Comprehensive command-line interface with colored output
- Full Python API for integration into existing workflows
- Detailed logging and error reporting

## Architecture Overview

```
PSD Character Extractor
├── Analyzer          # PSD structure analysis and layer detection
├── Extractor          # Expression extraction and compositing
├── Optimizer          # Image optimization and format conversion
├── Batch Processor    # Multi-file processing workflows
└── CLI Interface      # Command-line tools and user interaction
```

## Common Use Cases

### VTuber Setup
Extract lip sync expressions for real-time streaming applications:

```bash
# Extract all lip sync states
psd-extract character.psd --output ./vtuber-assets --format png

# Create optimized VTuber assets
psd-extract character.psd --output ./stream --optimize
```

### Game Development
Process multiple characters for a game project:

```bash
# Batch process all characters
psd-batch ./characters --output ./game-assets --workers 6 --report

# Use custom expression mapping
psd-extract character.psd --mapping ./custom-expressions.json
```

### Animation Pipeline
Extract all available expressions for animation work:

```bash
# Analyze character structure first
psd-analyze character.psd --detailed --output analysis.json

# Extract all expressions
psd-list-expressions character.psd
```

## Getting Started

1. **Installation**: See [Installation Guide](installation.md)
2. **First Steps**: Follow the [Quick Start Guide](quick-start.md)
3. **CLI Usage**: Check the [CLI Reference](cli-reference.md)
4. **Python Integration**: Review the [API Reference](api-reference.md)

## Community & Support

- **Issues**: [GitHub Issues](https://github.com/your-username/psd-character-extractor/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/psd-character-extractor/discussions)
- **Contributing**: See [CONTRIBUTING.md](../CONTRIBUTING.md)

## License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.