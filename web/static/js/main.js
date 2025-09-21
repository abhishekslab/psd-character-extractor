/**
 * PSD Character Extractor - Main JavaScript Application
 * Handles file upload, drag-and-drop mapping, and result management
 */

class PSDCharacterExtractor {
    constructor() {
        this.currentJobId = null;
        this.currentMapping = {};
        this.availableExpressions = [];
        this.mappingSuggestions = {};

        this.initializeElements();
        this.attachEventListeners();
        this.initializeDragAndDrop();
    }

    initializeElements() {
        // Upload elements
        this.uploadArea = document.getElementById('upload-area');
        this.fileInput = document.getElementById('file-input');
        this.uploadButton = document.getElementById('upload-button');
        this.uploadProgress = document.getElementById('upload-progress');
        this.progressFill = document.getElementById('progress-fill');
        this.progressText = document.getElementById('progress-text');
        this.progressPercent = document.getElementById('progress-percent');

        // Section elements
        this.uploadSection = document.getElementById('upload-section');
        this.analysisSection = document.getElementById('analysis-section');
        this.mappingSection = document.getElementById('mapping-section');
        this.resultsSection = document.getElementById('results-section');

        // Analysis elements
        this.psdInfo = document.getElementById('psd-info');

        // Mapping elements
        this.availableExpressionsContainer = document.getElementById('available-expressions');
        this.resetMappingButton = document.getElementById('reset-mapping');
        this.startExtractionButton = document.getElementById('start-extraction');

        // Results elements
        this.extractionProgress = document.getElementById('extraction-progress');
        this.extractionProgressFill = document.getElementById('extraction-progress-fill');
        this.extractionProgressText = document.getElementById('extraction-progress-text');
        this.extractionProgressPercent = document.getElementById('extraction-progress-percent');
        this.resultsContent = document.getElementById('results-content');
        this.resultsGrid = document.getElementById('results-grid');
        this.downloadButton = document.getElementById('download-button');

        // Utility elements
        this.statusMessages = document.getElementById('status-messages');
        this.loadingOverlay = document.getElementById('loading-overlay');
        this.loadingText = document.getElementById('loading-text');

        // Category containers
        this.categoryContainers = {
            'closed': document.getElementById('category-closed'),
            'small': document.getElementById('category-small'),
            'medium': document.getElementById('category-medium'),
            'wide': document.getElementById('category-wide')
        };
    }

    attachEventListeners() {
        // File upload events
        this.uploadButton.addEventListener('click', () => this.fileInput.click());
        this.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));

        // Upload area events
        this.uploadArea.addEventListener('click', () => this.fileInput.click());
        this.uploadArea.addEventListener('dragover', (e) => this.handleDragOver(e));
        this.uploadArea.addEventListener('dragleave', (e) => this.handleDragLeave(e));
        this.uploadArea.addEventListener('drop', (e) => this.handleFileDrop(e));

        // Mapping events
        this.resetMappingButton.addEventListener('click', () => this.resetMapping());
        this.startExtractionButton.addEventListener('click', () => this.startExtraction());

        // Download event
        this.downloadButton.addEventListener('click', () => this.downloadResults());
    }

    initializeDragAndDrop() {
        // Initialize drag and drop for expression mapping
        Object.keys(this.categoryContainers).forEach(category => {
            const container = this.categoryContainers[category];
            container.addEventListener('dragover', (e) => this.handleCategoryDragOver(e));
            container.addEventListener('dragleave', (e) => this.handleCategoryDragLeave(e));
            container.addEventListener('drop', (e) => this.handleCategoryDrop(e, category));
        });
    }

    // File Upload Methods
    handleDragOver(e) {
        e.preventDefault();
        this.uploadArea.classList.add('dragover');
    }

    handleDragLeave(e) {
        e.preventDefault();
        this.uploadArea.classList.remove('dragover');
    }

    handleFileDrop(e) {
        e.preventDefault();
        this.uploadArea.classList.remove('dragover');

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            this.processFileUpload(files[0]);
        }
    }

    handleFileSelect(e) {
        const file = e.target.files[0];
        if (file) {
            this.processFileUpload(file);
        }
    }

    async processFileUpload(file) {
        // Validate file
        if (!file.name.toLowerCase().endsWith('.psd')) {
            this.showStatusMessage('Only PSD files are allowed', 'error');
            return;
        }

        if (file.size > 100 * 1024 * 1024) { // 100MB limit
            this.showStatusMessage('File size must be less than 100MB', 'error');
            return;
        }

        try {
            this.showProgress(0, 'Uploading file...');

            // Create form data
            const formData = new FormData();
            formData.append('file', file);

            // Upload file
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`Upload failed: ${response.statusText}`);
            }

            const result = await response.json();
            this.currentJobId = result.job_id;

            this.showStatusMessage(`File uploaded successfully: ${file.name}`, 'success');
            this.showProgress(25, 'Analyzing PSD structure...');

            // Start polling for analysis results
            await this.pollJobStatus();

        } catch (error) {
            console.error('Upload error:', error);
            this.showStatusMessage(`Upload failed: ${error.message}`, 'error');
            this.hideProgress();
        }
    }

    // Job Status Polling
    async pollJobStatus() {
        const pollInterval = 2000; // 2 seconds

        const poll = async () => {
            try {
                const response = await fetch(`/api/job/${this.currentJobId}`);
                if (!response.ok) {
                    throw new Error(`Failed to get job status: ${response.statusText}`);
                }

                const job = await response.json();

                this.updateProgress(job.progress, this.getStatusMessage(job.status));

                switch (job.status) {
                    case 'ready_for_mapping':
                        await this.loadAnalysisResults();
                        break;
                    case 'completed':
                        await this.loadExtractionResults();
                        break;
                    case 'failed':
                        throw new Error(job.message || 'Job failed');
                    case 'pending':
                    case 'analyzing':
                    case 'extracting':
                        // Continue polling
                        setTimeout(poll, pollInterval);
                        break;
                }

            } catch (error) {
                console.error('Polling error:', error);
                this.showStatusMessage(`Error: ${error.message}`, 'error');
                this.hideProgress();
            }
        };

        await poll();
    }

    getStatusMessage(status) {
        const messages = {
            'pending': 'Preparing for analysis...',
            'analyzing': 'Analyzing PSD structure...',
            'ready_for_mapping': 'Analysis complete',
            'extracting': 'Extracting expressions...',
            'completed': 'Extraction complete',
            'failed': 'Processing failed'
        };
        return messages[status] || 'Processing...';
    }

    // Analysis Results
    async loadAnalysisResults() {
        try {
            const response = await fetch(`/api/analyze/${this.currentJobId}`);
            if (!response.ok) {
                throw new Error(`Failed to load analysis: ${response.statusText}`);
            }

            const analysis = await response.json();

            this.availableExpressions = analysis.available_expressions;
            this.mappingSuggestions = analysis.mapping_suggestions;
            this.currentMapping = { ...analysis.current_mapping };

            this.displayAnalysisResults(analysis.psd_info);
            this.displayExpressionMapping();
            this.showSection('mapping');
            this.hideProgress();

        } catch (error) {
            console.error('Analysis loading error:', error);
            this.showStatusMessage(`Failed to load analysis: ${error.message}`, 'error');
        }
    }

    displayAnalysisResults(psdInfo) {
        this.psdInfo.innerHTML = `
            <h3>File Information</h3>
            <div class="info-grid">
                <div class="info-item">
                    <span class="info-label">Dimensions:</span>
                    <span class="info-value">${psdInfo.width} × ${psdInfo.height} px</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Total Layers:</span>
                    <span class="info-value">${psdInfo.total_layers}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Color Mode:</span>
                    <span class="info-value">${psdInfo.color_mode}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Available Expressions:</span>
                    <span class="info-value">${this.availableExpressions.length}</span>
                </div>
            </div>
        `;

        this.showSection('analysis');
    }

    // Expression Mapping
    displayExpressionMapping() {
        // Clear existing content
        this.availableExpressionsContainer.innerHTML = '';
        Object.values(this.categoryContainers).forEach(container => {
            container.innerHTML = '';
        });

        // Create mapping sets for quick lookup
        const mappedExpressions = new Set();
        Object.values(this.currentMapping).forEach(expressions => {
            expressions.forEach(expr => mappedExpressions.add(expr));
        });

        // Display unmapped expressions
        const unmappedExpressions = this.availableExpressions.filter(expr =>
            !mappedExpressions.has(expr) || (this.currentMapping.unmapped && this.currentMapping.unmapped.includes(expr))
        );

        unmappedExpressions.forEach(expression => {
            this.availableExpressionsContainer.appendChild(
                this.createExpressionElement(expression)
            );
        });

        // Display mapped expressions
        Object.keys(this.categoryContainers).forEach(category => {
            if (this.currentMapping[category]) {
                this.currentMapping[category].forEach(expression => {
                    this.categoryContainers[category].appendChild(
                        this.createExpressionElement(expression)
                    );
                });
            }
        });
    }

    createExpressionElement(expressionName) {
        const element = document.createElement('div');
        element.className = 'expression-item';
        element.draggable = true;
        element.dataset.expression = expressionName;

        element.innerHTML = `
            <i class="fas fa-grip-vertical expression-icon"></i>
            <span>${expressionName}</span>
        `;

        // Add drag event listeners
        element.addEventListener('dragstart', (e) => this.handleExpressionDragStart(e));
        element.addEventListener('dragend', (e) => this.handleExpressionDragEnd(e));

        return element;
    }

    // Drag and Drop for Mapping
    handleExpressionDragStart(e) {
        e.dataTransfer.setData('text/plain', e.target.dataset.expression);
        e.target.classList.add('dragging');
    }

    handleExpressionDragEnd(e) {
        e.target.classList.remove('dragging');
    }

    handleCategoryDragOver(e) {
        e.preventDefault();
        e.currentTarget.parentElement.classList.add('drag-over');
    }

    handleCategoryDragLeave(e) {
        e.currentTarget.parentElement.classList.remove('drag-over');
    }

    handleCategoryDrop(e, category) {
        e.preventDefault();
        e.currentTarget.parentElement.classList.remove('drag-over');

        const expressionName = e.dataTransfer.getData('text/plain');
        if (!expressionName) return;

        // Remove from current location
        this.removeExpressionFromMapping(expressionName);

        // Add to new category
        if (!this.currentMapping[category]) {
            this.currentMapping[category] = [];
        }
        this.currentMapping[category].push(expressionName);

        // Refresh display
        this.displayExpressionMapping();

        // Update server mapping
        this.updateServerMapping();
    }

    removeExpressionFromMapping(expressionName) {
        Object.keys(this.currentMapping).forEach(category => {
            if (this.currentMapping[category]) {
                const index = this.currentMapping[category].indexOf(expressionName);
                if (index > -1) {
                    this.currentMapping[category].splice(index, 1);
                }
            }
        });
    }

    async updateServerMapping() {
        try {
            const response = await fetch(`/api/mapping/${this.currentJobId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    mapping: this.currentMapping
                })
            });

            if (!response.ok) {
                throw new Error(`Failed to update mapping: ${response.statusText}`);
            }

        } catch (error) {
            console.error('Mapping update error:', error);
            this.showStatusMessage(`Failed to update mapping: ${error.message}`, 'error');
        }
    }

    resetMapping() {
        this.currentMapping = { ...this.mappingSuggestions };
        this.displayExpressionMapping();
        this.updateServerMapping();
        this.showStatusMessage('Mapping reset to suggestions', 'success');
    }

    // Extraction
    async startExtraction() {
        try {
            this.showLoadingOverlay('Starting extraction...');

            const response = await fetch(`/api/extract/${this.currentJobId}`, {
                method: 'POST'
            });

            if (!response.ok) {
                throw new Error(`Failed to start extraction: ${response.statusText}`);
            }

            this.hideLoadingOverlay();
            this.showSection('results');
            this.showExtractionProgress(50, 'Extracting expressions...');

            // Start polling for extraction completion
            await this.pollJobStatus();

        } catch (error) {
            console.error('Extraction error:', error);
            this.showStatusMessage(`Extraction failed: ${error.message}`, 'error');
            this.hideLoadingOverlay();
        }
    }

    async loadExtractionResults() {
        try {
            const response = await fetch(`/api/results/${this.currentJobId}`);
            if (!response.ok) {
                throw new Error(`Failed to load results: ${response.statusText}`);
            }

            const results = await response.json();
            this.displayExtractionResults(results.results);
            this.hideExtractionProgress();

        } catch (error) {
            console.error('Results loading error:', error);
            this.showStatusMessage(`Failed to load results: ${error.message}`, 'error');
        }
    }

    displayExtractionResults(results) {
        this.resultsGrid.innerHTML = '';

        Object.keys(results).forEach(category => {
            const categoryResults = results[category];
            if (categoryResults.length > 0) {
                const categoryElement = document.createElement('div');
                categoryElement.className = 'result-category';
                categoryElement.innerHTML = `
                    <div class="result-category-header">
                        <h4>${category.charAt(0).toUpperCase() + category.slice(1)}</h4>
                    </div>
                    <div class="result-category-content">
                        ${categoryResults.map(result => `
                            <div class="result-item">
                                <i class="fas fa-check-circle result-icon"></i>
                                <span>${result.name}</span>
                            </div>
                        `).join('')}
                    </div>
                `;
                this.resultsGrid.appendChild(categoryElement);
            }
        });

        this.resultsContent.style.display = 'block';
    }

    // Download
    async downloadResults() {
        try {
            this.showLoadingOverlay('Preparing download...');

            const response = await fetch(`/api/download/${this.currentJobId}`);
            if (!response.ok) {
                throw new Error(`Download failed: ${response.statusText}`);
            }

            // Create download link
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `expressions_${this.currentJobId.substring(0, 8)}.zip`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            this.hideLoadingOverlay();
            this.showStatusMessage('Download started successfully', 'success');

        } catch (error) {
            console.error('Download error:', error);
            this.showStatusMessage(`Download failed: ${error.message}`, 'error');
            this.hideLoadingOverlay();
        }
    }

    // UI Utility Methods
    showSection(sectionName) {
        // Hide all sections
        [this.uploadSection, this.analysisSection, this.mappingSection, this.resultsSection]
            .forEach(section => section.style.display = 'none');

        // Show target section
        const sections = {
            'upload': this.uploadSection,
            'analysis': this.analysisSection,
            'mapping': this.mappingSection,
            'results': this.resultsSection
        };

        if (sections[sectionName]) {
            sections[sectionName].style.display = 'block';
            sections[sectionName].classList.add('fade-in');
        }
    }

    showProgress(percent, text) {
        this.uploadProgress.style.display = 'block';
        this.progressFill.style.width = `${percent}%`;
        this.progressText.textContent = text;
        this.progressPercent.textContent = `${Math.round(percent)}%`;
    }

    updateProgress(percent, text) {
        this.progressFill.style.width = `${percent}%`;
        this.progressText.textContent = text;
        this.progressPercent.textContent = `${Math.round(percent)}%`;
    }

    hideProgress() {
        this.uploadProgress.style.display = 'none';
    }

    showExtractionProgress(percent, text) {
        this.extractionProgress.style.display = 'block';
        this.extractionProgressFill.style.width = `${percent}%`;
        this.extractionProgressText.textContent = text;
        this.extractionProgressPercent.textContent = `${Math.round(percent)}%`;
    }

    hideExtractionProgress() {
        this.extractionProgress.style.display = 'none';
    }

    showLoadingOverlay(text) {
        this.loadingText.textContent = text;
        this.loadingOverlay.style.display = 'flex';
    }

    hideLoadingOverlay() {
        this.loadingOverlay.style.display = 'none';
    }

    showStatusMessage(message, type = 'info') {
        const messageElement = document.createElement('div');
        messageElement.className = `status-message ${type}`;
        messageElement.innerHTML = `
            <div>${message}</div>
        `;

        this.statusMessages.appendChild(messageElement);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (messageElement.parentNode) {
                messageElement.parentNode.removeChild(messageElement);
            }
        }, 5000);
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new PSDCharacterExtractor();
});