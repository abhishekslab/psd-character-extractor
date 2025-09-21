# Quick Start Guide

Get up and running with PSD Character Extractor in just a few minutes!

## Prerequisites

- Python 3.8 or higher
- A PSD file with character expressions (layered Photoshop file)

## Installation

### Option 1: Install from PyPI (Recommended)
```bash
pip install psd-character-extractor
```

### Option 2: Install from Source
```bash
git clone https://github.com/your-username/psd-character-extractor.git
cd psd-character-extractor
pip install -e .
```

## Your First Extraction

### Step 1: Analyze Your PSD File

First, let's see what expressions are available in your PSD file:

```bash
psd-analyze your-character.psd
```

This will show you:
- Basic PSD information (dimensions, layers)
- Detected expression layers
- Suggested layer groupings

### Step 2: List Available Expressions

Get a detailed list of all expression layers:

```bash
psd-list-expressions your-character.psd
```

Example output:
```
Available Expressions (8):
  • Normal
  • Smile
  • Smile 2
  • Delighted
  • Shocked
  • Laugh
  • Annoyed
  • Smug

Mappable to Lip Sync States:
  closed: Normal, Smug
  small: Smile, Smile 2
  medium: Delighted, Annoyed
  wide: Shocked, Laugh
```

### Step 3: Extract Expressions

Extract all lip sync expressions to PNG files:

```bash
psd-extract your-character.psd --output ./character-expressions
```

This will create:
```
character-expressions/
├── character-closed.png    # Normal or Smug expression
├── character-small.png     # Smile or Smile 2 expression
├── character-medium.png    # Delighted or Annoyed expression
└── character-wide.png      # Shocked or Laugh expression
```

## Common Options

### Custom Output Directory and Prefix
```bash
psd-extract character.psd --output ./assets --prefix "vtuber"
# Creates: vtuber-closed.png, vtuber-small.png, etc.
```

### Specific Expressions Only
```bash
psd-extract character.psd --states closed small --output ./minimal
# Only extracts closed and small mouth states
```

### Different Output Format
```bash
psd-extract character.psd --format webp --output ./optimized
# Outputs WebP format instead of PNG
```

### Skip Optimization (Faster)
```bash
psd-extract character.psd --no-optimize --output ./raw
# Skips image optimization for faster processing
```

## Working with Multiple Files

### Batch Process a Directory
```bash
psd-batch ./psd-files --output ./all-characters --workers 4 --report
```

This will:
- Process all PSD files in `./psd-files`
- Use 4 worker threads for parallel processing
- Generate a processing report
- Create separate folders for each character

### Custom Expression Mapping

Create a custom mapping file:

```bash
psd-create-mapping --output my-expressions.json
```

Edit the generated file:
```json
{
  "closed": ["neutral", "calm", "resting"],
  "small": ["slight_smile", "content"],
  "medium": ["talking", "explaining"],
  "wide": ["excited", "shouting", "singing"]
}
```

Use your custom mapping:
```bash
psd-extract character.psd --mapping my-expressions.json --output ./custom
```

## Integration Examples

### VTuber Streaming Setup

For real-time streaming applications:

```bash
# Extract optimized expressions for VTuber use
psd-extract character.psd \
  --output ./stream-assets \
  --prefix "avatar" \
  --format png \
  --optimize

# Verify the extracted files
ls -la stream-assets/
# avatar-closed.png  (for silent moments)
# avatar-small.png   (for quiet speech)
# avatar-medium.png  (for normal speech)
# avatar-wide.png    (for loud speech/singing)
```

### Game Development Pipeline

For game character assets:

```bash
# Process all character PSD files
psd-batch ./game-characters \
  --output ./game-assets \
  --mapping ./game-expressions.json \
  --workers 6 \
  --report

# This creates organized assets:
# game-assets/
# ├── protagonist/
# │   ├── protagonist-closed.png
# │   └── ...
# ├── sidekick/
# │   ├── sidekick-closed.png
# │   └── ...
# └── batch_report.txt
```

## Troubleshooting

### "No expression layers found"

This usually means your PSD doesn't use standard naming. Try:

1. Check layer names with detailed analysis:
   ```bash
   psd-analyze character.psd --detailed --output analysis.json
   ```

2. Create a custom mapping that matches your layer names:
   ```bash
   psd-create-mapping --output custom.json
   # Edit custom.json to match your layer names
   psd-extract character.psd --mapping custom.json
   ```

### "Failed to extract expression"

Common causes:
- Expression layer is inside a hidden group
- Layer name doesn't match mapping exactly (case-sensitive)
- PSD file is corrupted or unsupported format

Try the detailed analysis to debug:
```bash
psd-analyze character.psd --detailed
```

### Performance Issues

For large PSD files or batch processing:

```bash
# Reduce worker count if system is struggling
psd-batch ./files --workers 2

# Skip optimization for speed
psd-extract file.psd --no-optimize

# Use JPEG for smaller file sizes
psd-extract file.psd --format jpg
```

## Next Steps

- Read the [CLI Reference](cli-reference.md) for all available commands
- Check the [Python API Reference](api-reference.md) for programmatic usage
- Learn about [Expression Mapping](expression-mapping.md) for custom configurations
- Explore [Batch Processing](batch-processing.md) for workflow automation

## Need Help?

- Check the [Troubleshooting Guide](troubleshooting.md)
- Search [existing issues](https://github.com/your-username/psd-character-extractor/issues)
- Start a [discussion](https://github.com/your-username/psd-character-extractor/discussions)