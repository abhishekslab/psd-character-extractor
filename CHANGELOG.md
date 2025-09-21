# Changelog

All notable changes to PSD Character Extractor will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release of PSD Character Extractor
- Core PSD analysis and layer detection functionality
- Character expression extraction with lip sync mapping
- Image optimization for web and VTuber applications
- Comprehensive CLI interface with multiple commands
- Batch processing support for multiple PSD files
- Professional documentation and examples
- Complete test suite with CI/CD pipeline

### Features
- **PSD Analysis**: Intelligent layer structure analysis and expression detection
- **Expression Extraction**: Map PSD layers to lip sync states (closed, small, medium, wide)
- **Image Optimization**: Web-optimized output with configurable quality and formats
- **Batch Processing**: Multi-threaded processing of multiple PSD files
- **CLI Tools**: Full command-line interface with colored output and progress tracking
- **VTuber Integration**: Specialized optimization for VTuber and streaming applications
- **Game Development**: Tools and workflows for game character asset creation
- **Custom Mapping**: JSON-based expression mapping for flexible layer organization

### CLI Commands
- `psd-analyze`: Analyze PSD file structure and identify expressions
- `psd-extract`: Extract character expressions to image files
- `psd-batch`: Batch process multiple PSD files
- `psd-list-expressions`: List all available expressions in a PSD
- `psd-create-mapping`: Create expression mapping templates

### Supported Formats
- **Input**: PSD, PSB (Photoshop files)
- **Output**: PNG, JPEG, WebP

### Python API
- `CharacterExtractor`: Main extraction class
- `PSDAnalyzer`: PSD structure analysis
- `ImageOptimizer`: Image optimization and format conversion
- `BatchProcessor`: Multi-file processing workflows

### Documentation
- Comprehensive user documentation
- API reference
- CLI command reference
- Integration examples for VTuber and game development
- Quick start guide and tutorials

### Examples
- Basic usage examples
- VTuber integration workflows
- Game development pipelines
- Custom optimization configurations

## [0.1.0] - 2024-01-XX

### Added
- Initial project structure
- Core functionality implementation
- Basic CLI interface
- Documentation framework

---

## Release Planning

### [0.2.0] - Planned
- Performance optimizations
- Additional output formats
- Enhanced error handling
- More expression mapping presets

### [0.3.0] - Planned
- GUI application
- Real-time preview
- Plugin system
- Advanced animation features

### [1.0.0] - Planned
- Stable API
- Complete feature set
- Production-ready release
- Full documentation

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for information on how to contribute to this project.

## Support

For questions, bug reports, or feature requests:
- [GitHub Issues](https://github.com/psd-extractor/psd-character-extractor/issues)
- [GitHub Discussions](https://github.com/psd-extractor/psd-character-extractor/discussions)
- [Documentation](https://psd-character-extractor.readthedocs.io/)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.