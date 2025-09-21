# CLI Reference

Complete command-line interface reference for PSD Character Extractor.

## Global Options

All commands support these global options:

- `--verbose, -v`: Enable verbose output with debug information
- `--quiet, -q`: Suppress non-error output
- `--help`: Show help information for any command

## Commands Overview

| Command | Purpose |
|---------|---------|
| [`psd-analyze`](#psd-analyze) | Analyze PSD structure and identify expressions |
| [`psd-extract`](#psd-extract) | Extract character expressions to image files |
| [`psd-batch`](#psd-batch) | Batch process multiple PSD files |
| [`psd-list-expressions`](#psd-list-expressions) | List all available expressions in a PSD |
| [`psd-create-mapping`](#psd-create-mapping) | Create expression mapping template |

## psd-analyze

Analyze PSD file structure and identify expression layers.

### Usage
```bash
psd-analyze PSD_FILE [OPTIONS]
```

### Arguments
- `PSD_FILE`: Path to the PSD file to analyze (required)

### Options
- `--detailed, -d`: Show detailed layer analysis including full layer tree
- `--output, -o PATH`: Save analysis results to JSON file

### Examples

**Basic analysis:**
```bash
psd-analyze character.psd
```

**Detailed analysis with JSON output:**
```bash
psd-analyze character.psd --detailed --output analysis.json
```

### Sample Output

**Basic Analysis:**
```
ℹ Analyzing PSD file: character.psd

PSD Analysis Report: character.psd
==================================================
Dimensions: 1024 x 1536
Color Mode: ColorMode.RGB
Total Layers: 45

Potential Expression Layers (8):
  - Normal (keywords: neutral)
  - Smile (keywords: smile, happy)
  - Smile 2 (keywords: smile, happy)
  - Delighted (keywords: delighted, happy)
  - Shocked (keywords: shocked, surprised)
  - Laugh (keywords: laugh, happy)
  - Annoyed (keywords: annoyed)
  - Smug (keywords: smug)

Layer Groups:
  Expression: 8 layers
  Hair: 3 layers
  Costume: 5 layers

==================================================
✓ Analysis complete
```

**Detailed Analysis JSON Structure:**
```json
{
  "basic_info": {
    "width": 1024,
    "height": 1536,
    "color_mode": "ColorMode.RGB",
    "total_layers": 45,
    "file_path": "character.psd"
  },
  "layer_tree": [...],
  "expression_analysis": [
    {
      "name": "Normal",
      "keywords": ["neutral"],
      "visible": true,
      "width": 200,
      "height": 100
    }
  ],
  "layer_groups": {
    "expression": ["Normal", "Smile", "Shocked"],
    "hair": ["Hair Base", "Hair Highlights"],
    "costume": ["Dress", "Accessories"]
  }
}
```

## psd-extract

Extract character expressions from PSD file to image files.

### Usage
```bash
psd-extract PSD_FILE [OPTIONS]
```

### Arguments
- `PSD_FILE`: Path to the PSD file to extract from (required)

### Options
- `--output, -o PATH`: Output directory for extracted images (default: `./output`)
- `--mapping, -m PATH`: JSON file with custom expression mapping
- `--states, -s STATE`: Specific lip sync states to extract (can be used multiple times)
- `--prefix, -p TEXT`: Prefix for output filenames (default: `character`)
- `--no-optimize`: Skip image optimization (faster processing)
- `--format FORMAT`: Output image format: `png`, `jpg`, `webp` (default: `png`)

### Examples

**Basic extraction:**
```bash
psd-extract character.psd
# Creates: ./output/character-closed.png, character-small.png, etc.
```

**Custom output directory and prefix:**
```bash
psd-extract character.psd --output ./vtuber-assets --prefix "avatar"
# Creates: ./vtuber-assets/avatar-closed.png, avatar-small.png, etc.
```

**Extract specific states only:**
```bash
psd-extract character.psd --states closed --states small --output ./minimal
# Only extracts closed and small mouth states
```

**Use custom expression mapping:**
```bash
psd-extract character.psd --mapping ./custom-expressions.json --output ./custom
```

**WebP output with no optimization:**
```bash
psd-extract character.psd --format webp --no-optimize --output ./fast
```

### Sample Output
```
ℹ Extracting from PSD file: character.psd
ℹ Found 4 extractable lip sync states
ℹ Extracting for lip sync state: closed
ℹ   ✓ Used 'Normal' for closed state
ℹ Extracting for lip sync state: small
ℹ   ✓ Used 'Smile' for small state
ℹ Extracting for lip sync state: medium
ℹ   ✓ Used 'Delighted' for medium state
ℹ Extracting for lip sync state: wide
ℹ   ✓ Used 'Shocked' for wide state
✓ Successfully extracted 4 expressions:
  • closed: ./output/character-closed.png
  • small: ./output/character-small.png
  • medium: ./output/character-medium.png
  • wide: ./output/character-wide.png
✓ Output saved to: ./output
```

## psd-batch

Batch process multiple PSD files in a directory.

### Usage
```bash
psd-batch INPUT_DIR [OPTIONS]
```

### Arguments
- `INPUT_DIR`: Directory containing PSD files (required)

### Options
- `--output, -o PATH`: Output directory for all extracted images (required)
- `--mapping, -m PATH`: JSON file with expression mapping for all files
- `--workers, -w NUMBER`: Number of concurrent workers (default: 4)
- `--report`: Generate processing report

### Examples

**Basic batch processing:**
```bash
psd-batch ./characters --output ./game-assets
```

**High-performance processing with report:**
```bash
psd-batch ./characters --output ./assets --workers 8 --report
```

**With custom mapping:**
```bash
psd-batch ./characters --output ./assets --mapping ./game-expressions.json --report
```

### Sample Output
```
ℹ Starting batch processing: ./characters
ℹ Found 3 PSD files to process
Extracting characters: 100%|██████████| 3/3 [00:45<00:00, 15.2s/it]
✓ All 3 files processed successfully
✓ Report saved to: ./assets/batch_report.txt
✓ Batch processing complete. Output in: ./assets
```

### Output Structure
```
assets/
├── character1/
│   ├── character1-closed.png
│   ├── character1-small.png
│   ├── character1-medium.png
│   └── character1-wide.png
├── character2/
│   ├── character2-closed.png
│   └── ...
├── character3/
│   └── ...
└── batch_report.txt
```

### Batch Report Example
```
Batch Processing Report
==================================================
Total files processed: 3
Successful extractions: 3
Failed extractions: 0

Per-file Results:
------------------------------
✓ character1.psd: 4 expressions extracted
✓ character2.psd: 4 expressions extracted
✓ character3.psd: 3 expressions extracted
```

## psd-list-expressions

List all available expression layers in a PSD file.

### Usage
```bash
psd-list-expressions PSD_FILE
```

### Arguments
- `PSD_FILE`: Path to the PSD file to analyze (required)

### Examples

**List expressions:**
```bash
psd-list-expressions character.psd
```

### Sample Output
```
ℹ Listing expressions in: character.psd

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

## psd-create-mapping

Create a template expression mapping file for custom configurations.

### Usage
```bash
psd-create-mapping [OPTIONS]
```

### Options
- `--output, -o PATH`: Output file for the mapping template (default: `expression_mapping.json`)

### Examples

**Create default mapping template:**
```bash
psd-create-mapping
```

**Custom output file:**
```bash
psd-create-mapping --output ./my-game-expressions.json
```

### Sample Output
```
✓ Expression mapping template created: expression_mapping.json
ℹ Edit this file to match your PSD layer names
```

### Generated Template
```json
{
  "_comment": "Expression mapping for lip sync states",
  "_description": "Map lip sync states to PSD layer names",
  "closed": [
    "normal",
    "neutral",
    "smug",
    "calm"
  ],
  "small": [
    "smile",
    "smile 2",
    "happy",
    "pleased"
  ],
  "medium": [
    "delighted",
    "excited",
    "annoyed",
    "talking"
  ],
  "wide": [
    "shocked",
    "surprised",
    "laugh",
    "amazed"
  ],
  "_examples": {
    "custom_state": [
      "layer_name_1",
      "layer_name_2"
    ]
  }
}
```

## Error Handling

All commands use consistent error reporting:

### Success Messages
- ✓ Green checkmark for successful operations
- ℹ Blue info icon for informational messages

### Warnings
- ⚠ Yellow warning icon for non-critical issues
- Example: "No extractable expressions found"

### Errors
- ✗ Red X for errors that prevent operation
- Exit codes: 0 (success), 1 (error)

### Common Exit Codes
- `0`: Success
- `1`: File not found, invalid arguments, or processing errors

## Performance Tips

### For Large Files
- Use `--no-optimize` for faster processing during development
- Reduce `--workers` count if system memory is limited

### For Batch Processing
- Use more `--workers` on systems with more CPU cores
- Process files in smaller batches if memory usage becomes an issue

### For Web Deployment
- Use `--format webp` for smaller file sizes
- Keep optimization enabled for production assets

## Environment Variables

- `PSD_EXTRACTOR_LOG_LEVEL`: Set to `DEBUG` for detailed logging
- `PSD_EXTRACTOR_WORKERS`: Default number of workers for batch processing

Example:
```bash
export PSD_EXTRACTOR_LOG_LEVEL=DEBUG
psd-extract character.psd --verbose
```