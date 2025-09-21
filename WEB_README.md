# PSD Character Extractor - Web Interface

A modern web interface for the PSD Character Extractor that provides drag-and-drop functionality for uploading PSD files, mapping expressions to lip sync states, and downloading the extracted results.

## Features

- **Drag & Drop Upload**: Simply drag your PSD file to the upload area
- **Automatic Analysis**: Analyzes PSD structure and identifies expression layers
- **Interactive Mapping**: Drag and drop expressions to appropriate lip sync categories
- **Real-time Progress**: Visual progress indicators for all operations
- **Easy Download**: Download extracted expressions as a ZIP file

## Installation

1. Install the web dependencies:
```bash
pip install -e ".[web]"
```

2. Start the web server:
```bash
psd-web
```

3. Open your browser and navigate to:
```
http://localhost:8000
```

## Usage

### Step 1: Upload PSD File
- Drag and drop your PSD file onto the upload area, or click to browse files
- Only .psd files are supported (up to 100MB)
- The system will automatically analyze the file structure

### Step 2: Review Analysis
- View basic information about your PSD file
- See the total number of layers and detected expressions

### Step 3: Map Expressions
- Available expressions are shown on the left panel
- Drag expressions from the available list to the appropriate lip sync categories:
  - **Closed**: Mouth closed, neutral expressions (normal, neutral, etc.)
  - **Small**: Slight mouth opening, smiles (smile, happy, etc.)
  - **Medium**: Medium mouth opening, talking (delighted, talking, etc.)
  - **Wide**: Wide mouth opening, surprise, laughter (shocked, laugh, etc.)
- The system provides automatic mapping suggestions based on layer names
- You can reset to suggestions or manually adjust the mapping

### Step 4: Extract and Download
- Click "Start Extraction" to begin processing
- Monitor the extraction progress
- Once complete, download the ZIP file containing all extracted expressions

## File Organization

Extracted expressions are organized in the ZIP file by category:
```
expressions_12345678.zip
├── closed_normal.png
├── closed_neutral.png
├── small_smile.png
├── small_happy.png
├── medium_talking.png
├── wide_shocked.png
└── ...
```

## API Endpoints

The web interface provides a REST API for programmatic access:

- `POST /api/upload` - Upload PSD file
- `GET /api/job/{job_id}` - Get job status
- `GET /api/analyze/{job_id}` - Get analysis results
- `POST /api/mapping/{job_id}` - Update expression mapping
- `POST /api/extract/{job_id}` - Start extraction
- `GET /api/results/{job_id}` - Get extraction results
- `GET /api/download/{job_id}` - Download results

## Development

### Running in Development Mode

1. Install development dependencies:
```bash
pip install -e ".[dev,web]"
```

2. Start the development server:
```bash
uvicorn psd_extractor.web_api:app --reload --host 0.0.0.0 --port 8000
```

### Architecture

The web interface consists of:

- **FastAPI Backend**: Async REST API with background job processing
- **Job Management**: Handles file uploads, processing queue, and cleanup
- **Async Extractor**: Non-blocking wrapper for PSD processing operations
- **Modern Frontend**: Vanilla JavaScript with drag-and-drop functionality

### File Structure

```
web/
├── static/
│   ├── css/style.css      # Main stylesheet
│   └── js/main.js         # JavaScript application
├── templates/
│   └── index.html         # Main HTML template
└── uploads/               # Temporary file storage

src/psd_extractor/
├── web_api.py            # FastAPI application
└── utils/
    ├── async_extractor.py # Async wrapper
    └── job_manager.py     # Job management
```

## Production Deployment

For production deployment, consider:

1. **Reverse Proxy**: Use nginx or similar for static file serving
2. **Process Manager**: Use gunicorn with multiple workers
3. **File Storage**: Configure appropriate storage for uploads and results
4. **Monitoring**: Add health checks and monitoring
5. **Security**: Implement authentication if needed

Example production command:
```bash
gunicorn psd_extractor.web_api:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Browser Support

The web interface supports modern browsers with:
- HTML5 File API
- Drag and Drop API
- Fetch API
- ES6+ JavaScript features

Tested on:
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Troubleshooting

### Common Issues

1. **Upload Fails**: Check file size (max 100MB) and format (.psd only)
2. **Analysis Timeout**: Large PSD files may take several minutes to analyze
3. **Extraction Errors**: Ensure PSD has proper layer structure with expression groups
4. **Download Issues**: Check browser download settings and available disk space

### Logs

Check the console output for detailed error messages and processing logs.

### Support

For issues and feature requests, please visit the main project repository.