# PSD Character Extractor

**Automated character extraction from Photoshop PSD files for VTubers, game development, and animation workflows.**

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/psd-character-extractor.svg)](https://badge.fury.io/py/psd-character-extractor)

## ✨ Features

- **🤖 Automated Layer Detection** - Intelligently analyzes PSD structure and identifies character expressions
- **🎭 Expression Mapping** - Maps facial expressions to lip sync states for animation
- **⚡ Batch Processing** - Process multiple characters and expression sets efficiently
- **🌐 Web Optimization** - Automatically optimizes output images for web applications
- **🎮 VTuber Ready** - Purpose-built for VTuber avatar systems and live streaming
- **📦 Easy Integration** - Simple Python API and command-line interface

## 🚀 Quick Start

### Installation

```bash
pip install psd-character-extractor
```

### Basic Usage

```python
from psd_extractor import CharacterExtractor

# Extract character expressions for lip sync
extractor = CharacterExtractor("character.psd")
expressions = extractor.extract_expressions({
    'closed': ['normal', 'neutral'],
    'small': ['smile', 'happy'],
    'medium': ['delighted', 'excited'],
    'wide': ['shocked', 'surprised']
})

# Save optimized images
extractor.save_expressions(expressions, output_dir="./character_output")
```

### Command Line

```bash
# Basic extraction
psd-extract character.psd --output ./output

# Custom expression mapping
psd-extract character.psd --config expressions.json --batch

# Analyze PSD structure
psd-analyze character.psd --verbose
```

## 🎯 Use Cases

### VTuber Avatars
- Extract multiple facial expressions for live streaming
- Optimize for real-time lip sync animation
- Batch process character variants (outfits, hairstyles)

### Game Development
- Convert character art assets to game-ready sprites
- Generate expression sets for dialogue systems
- Automate character customization pipelines

### Animation Workflows
- Extract layered character components
- Prepare assets for 2D animation software
- Maintain consistent character proportions

## 📖 Documentation

- [Installation Guide](docs/installation.md)
- [Usage Examples](docs/usage.md)
- [API Reference](docs/api-reference.md)
- [Expression Mapping](docs/expression-mapping.md)
- [VTuber Integration](docs/vtuber-integration.md)

## 🎨 Example Output

| Input PSD | Extracted Expressions |
|-----------|----------------------|
| ![Character PSD](assets/demo-input.png) | ![Expressions](assets/demo-output.png) |

*Professional anime character with multiple expressions extracted automatically*

## 🛠️ Advanced Features

### Custom Expression Mapping
```python
# Define custom expression mapping
mapping = {
    'talking': ['smile', 'happy', 'excited'],
    'silent': ['normal', 'neutral', 'calm'],
    'surprised': ['shocked', 'amazed', 'wow'],
    'emotional': ['sad', 'crying', 'upset']
}

extractor.set_expression_mapping(mapping)
```

### Batch Processing
```python
# Process multiple PSD files
from psd_extractor import BatchProcessor

processor = BatchProcessor(
    input_dir="./characters",
    output_dir="./extracted",
    mapping_file="expressions.json"
)

results = processor.process_all()
```

### Web Optimization
```python
# Configure output optimization
extractor.set_optimization({
    'format': 'PNG',
    'width': 400,
    'height': 600,
    'quality': 85,
    'compress': True
})
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](docs/contributing.md) for details.

### Development Setup

```bash
git clone https://github.com/yourusername/psd-character-extractor.git
cd psd-character-extractor
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest tests/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [psd-tools](https://github.com/psd-tools/psd-tools) for PSD file parsing
- Inspired by the VTuber and indie game development communities
- Special thanks to character artists who make this workflow possible

## 📞 Support

- 📖 [Documentation](docs/)
- 🐛 [Issue Tracker](https://github.com/yourusername/psd-character-extractor/issues)
- 💬 [Discussions](https://github.com/yourusername/psd-character-extractor/discussions)

---

**Made with ❤️ for the creative community**