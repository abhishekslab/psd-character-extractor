# Examples

This directory contains comprehensive examples demonstrating how to use PSD Character Extractor in various scenarios and workflows.

## Available Examples

### 📚 [basic_usage.py](basic_usage.py)
**Foundation examples for getting started**

Learn the core functionality through 7 practical examples:
- Basic expression extraction with default settings
- Custom expression mapping for specific use cases
- Selective extraction (only specific expressions)
- Image optimization and format options
- PSD structure analysis and layer detection
- Batch processing multiple files
- Extracting all available expressions

**Best for**: First-time users, learning the API, understanding core concepts

**Run with**: `python basic_usage.py`

### 🎭 [vtuber_integration.py](vtuber_integration.py)
**VTuber and streaming application examples**

Specialized examples for VTuber and streaming setups:
- OBS Studio integration workflow
- VTube Studio asset preparation
- Complete streaming workflow (multiple quality levels)
- Real-time lip sync simulation
- Sprite sheet generation for streaming software

**Best for**: VTubers, streamers, content creators

**Run with**: `python vtuber_integration.py`

### 🎮 [game_development.py](game_development.py)
**Game development pipeline examples**

Comprehensive game development workflows:
- Dialogue system character setup
- RPG character roster management
- Visual novel expression systems
- Asset validation and quality assurance
- Multi-character batch processing

**Best for**: Game developers, indie studios, visual novel creators

**Run with**: `python game_development.py`

## Prerequisites

Before running the examples, ensure you have:

1. **Python Environment**: Python 3.8+ with PSD Character Extractor installed
2. **Sample PSD Files**: The examples expect PSD files with specific names:
   - `character.psd` - Main character file for basic examples
   - `protagonist.psd` - For dialogue system examples
   - `companion.psd` - For multi-character examples
   - Additional character PSD files for game development examples

3. **Directory Structure**: Some examples expect certain directory structures:
   ```
   your-project/
   ├── character.psd
   ├── protagonist.psd
   ├── companion.psd
   ├── psd_files/          # For batch processing examples
   │   ├── character1.psd
   │   ├── character2.psd
   │   └── ...
   └── examples/
       ├── basic_usage.py
       ├── vtuber_integration.py
       └── game_development.py
   ```

## Quick Start

### Option 1: Run Individual Examples

```bash
# Navigate to examples directory
cd examples

# Run basic usage examples
python basic_usage.py

# Run VTuber-specific examples
python vtuber_integration.py

# Run game development examples
python game_development.py
```

### Option 2: Run Specific Example Functions

You can also import and run specific examples:

```python
from basic_usage import example_basic_extraction
from vtuber_integration import example_obs_integration
from game_development import example_dialogue_system_setup

# Run only the examples you need
example_basic_extraction()
example_obs_integration()
example_dialogue_system_setup()
```

## Example Output Structure

Each example creates organized output directories:

```
./
├── basic_output/                 # Basic usage outputs
│   ├── character-closed.png
│   ├── character-small.png
│   └── ...
├── vtuber_assets/               # VTuber-optimized assets
│   ├── vtuber_closed.png
│   ├── vtuber_sprite_sheet.png
│   └── vtuber_config.json
├── game_assets/                 # Game development assets
│   ├── characters/
│   │   ├── protagonist/
│   │   └── companion/
│   └── config/
│       ├── dialogue_config.json
│       └── rpg_roster.json
└── analysis_files/              # Analysis and reports
    ├── psd_analysis.json
    ├── batch_report.txt
    └── validation_report.json
```

## Customizing Examples

### Modify File Paths

Update the PSD file paths in each example to match your files:

```python
# Change this
psd_file = "character.psd"

# To your actual file path
psd_file = "/path/to/your/character.psd"
```

### Adjust Output Directories

Customize output locations for your workflow:

```python
# Change output directory
output_dir = "./your_custom_output"

# Or use absolute paths
output_dir = "/full/path/to/assets"
```

### Customize Expression Mappings

Create custom mappings for your specific PSD layer structure:

```python
custom_mapping = {
    'state_name': ['layer_name_1', 'layer_name_2'],
    'happy': ['smile', 'joy', 'cheerful'],
    'sad': ['sad', 'crying', 'melancholy']
}
```

## Common Issues and Solutions

### "PSD file not found"
**Problem**: Examples can't find the specified PSD files.
**Solution**:
- Update file paths in the examples to match your PSD file locations
- Ensure PSD files exist and are readable
- Use absolute paths if relative paths aren't working

### "No expressions found"
**Problem**: The extractor can't find expression layers in your PSD.
**Solution**:
- Run the analysis example first to see available layers
- Create custom expression mapping that matches your layer names
- Check that your PSD has layers with expression-related keywords

### "Permission denied" or "Directory not found"
**Problem**: Can't create output directories or save files.
**Solution**:
- Ensure you have write permissions in the output directories
- Create output directories manually if needed
- Check available disk space

### "Import errors"
**Problem**: Can't import psd_extractor modules.
**Solution**:
- Ensure PSD Character Extractor is properly installed: `pip install psd-character-extractor`
- Check Python path and virtual environment
- Install from source if needed: `pip install -e .`

## Performance Tips

### For Large PSD Files
- Use selective extraction (only needed expressions)
- Skip optimization during development: `optimize=False`
- Reduce target image sizes for faster processing

### For Batch Processing
- Adjust worker count based on your system: `max_workers=2` for slower systems
- Process files in smaller batches if memory is limited
- Use SSD storage for better I/O performance

### For Production Use
- Enable optimization for final assets
- Use appropriate image formats (PNG for transparency, JPEG for smaller files)
- Validate all assets after processing

## Integration Workflows

### VTuber Streaming Setup
1. Run `vtuber_integration.py` to create optimized assets
2. Import assets into OBS Studio or VTube Studio
3. Configure audio-reactive switching
4. Test with streaming software

### Game Development Pipeline
1. Run analysis examples to understand PSD structure
2. Create custom expression mappings for your game
3. Use batch processing for multiple characters
4. Validate assets before integration
5. Import into game engine (Unity, Godot, etc.)

### Custom Application Development
1. Study the Python API examples in `basic_usage.py`
2. Create custom extraction workflows using the library
3. Implement real-time expression switching
4. Add error handling and logging for production use

## Contributing Examples

Have a useful example or workflow? We'd love to include it!

1. Create a new example file following the existing pattern
2. Include comprehensive documentation and error handling
3. Add the example to this README
4. Submit a pull request

Example contributions could include:
- Mobile app integration examples
- Web development workflows
- Animation software integration
- AI/ML training data preparation
- Custom optimization pipelines

## Support

If you encounter issues with the examples:

1. Check the [Troubleshooting Guide](../docs/troubleshooting.md)
2. Review the [API Documentation](../docs/api-reference.md)
3. Search [existing issues](https://github.com/your-username/psd-character-extractor/issues)
4. Create a new issue with your example code and error messages

## License

All examples are provided under the same MIT License as the main project.