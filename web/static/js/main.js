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
        this.allComponents = {};
        this.extractableComponents = [];
        this.currentComponentCategory = 'expression';
        this.selectedComponents = new Set();
        this.isLegacyMode = false;
        this.rawLayers = [];
        this.isRawLayersMode = false;

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
        this.psdCompositeImage = document.getElementById('psd-composite-image');
        this.previewLoading = document.getElementById('preview-loading');
        this.previewError = document.getElementById('preview-error');

        // Component management elements
        this.componentTabs = document.getElementById('component-tabs');
        this.componentBrowserContent = document.getElementById('component-browser-content');
        this.toggleLegacyModeButton = document.getElementById('toggle-legacy-mode');
        this.extractAllComponentsCheckbox = document.getElementById('extract-all-components');
        this.extractExpressionsOnlyCheckbox = document.getElementById('extract-expressions-only');

        // Mapping elements (legacy)
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

        // Component management events
        this.toggleLegacyModeButton.addEventListener('click', () => this.toggleLegacyMode());
        this.extractAllComponentsCheckbox.addEventListener('change', (e) => this.handleExtractionModeChange(e));
        this.extractExpressionsOnlyCheckbox.addEventListener('change', (e) => this.handleExtractionModeChange(e));

        // Mapping events (legacy)
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
            this.allComponents = analysis.all_components || {};
            this.extractableComponents = analysis.extractable_components || [];

            this.displayAnalysisResults(analysis.psd_info);
            this.displayComponentManagement();
            this.loadRawLayers(); // Load raw layers in parallel
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

        // Load and display preview image
        this.loadCompositePreview();

        this.showSection('analysis');
    }

    async loadCompositePreview() {
        try {
            // Show loading state
            this.previewLoading.style.display = 'flex';
            this.previewError.style.display = 'none';
            this.psdCompositeImage.style.display = 'none';

            // Construct preview URL
            const previewUrl = `/api/preview/${this.currentJobId}/composite`;

            // Set image source and handle loading
            this.psdCompositeImage.onload = () => {
                this.previewLoading.style.display = 'none';
                this.psdCompositeImage.style.display = 'block';
            };

            this.psdCompositeImage.onerror = () => {
                this.previewLoading.style.display = 'none';
                this.previewError.style.display = 'flex';
                console.error('Failed to load composite preview');
            };

            // Load the image
            this.psdCompositeImage.src = previewUrl;

        } catch (error) {
            console.error('Error loading composite preview:', error);
            this.previewLoading.style.display = 'none';
            this.previewError.style.display = 'flex';
        }
    }

    // Component Management
    displayComponentManagement() {
        // Show component interface by default, hide legacy
        this.showComponentInterface();
        this.displayComponentTabs();
        this.displayComponentGrid(this.currentComponentCategory);
    }

    showComponentInterface() {
        const componentBrowser = document.querySelector('.component-browser');
        const legacyPanel = document.querySelector('.legacy-panel');

        if (componentBrowser) componentBrowser.style.display = 'block';
        if (legacyPanel) legacyPanel.style.display = 'none';

        this.isLegacyMode = false;
        this.updateToggleButton();
    }

    showLegacyInterface() {
        const componentBrowser = document.querySelector('.component-browser');
        const legacyPanel = document.querySelector('.legacy-panel');

        if (componentBrowser) componentBrowser.style.display = 'none';
        if (legacyPanel) legacyPanel.style.display = 'block';

        this.isLegacyMode = true;
        this.updateToggleButton();
        this.displayExpressionMapping();
    }

    updateToggleButton() {
        if (this.toggleLegacyModeButton) {
            const icon = this.toggleLegacyModeButton.querySelector('i');
            const text = this.isLegacyMode ? 'Component Mode' : 'Expression Mode';

            this.toggleLegacyModeButton.innerHTML = `<i class="fas fa-exchange-alt"></i> ${text}`;
        }
    }

    displayComponentTabs() {
        if (!this.componentTabs) return;

        this.componentTabs.innerHTML = '';

        // Get categories with components
        const categoriesWithComponents = Object.keys(this.allComponents).filter(
            category => this.allComponents[category] && this.allComponents[category].length > 0
        );

        // Ensure expressions is first if it exists
        if (categoriesWithComponents.includes('expression')) {
            categoriesWithComponents.sort((a, b) => {
                if (a === 'expression') return -1;
                if (b === 'expression') return 1;
                return a.localeCompare(b);
            });
        }

        categoriesWithComponents.forEach(category => {
            const tab = document.createElement('button');
            tab.className = `browser-tab ${category === this.currentComponentCategory ? 'active' : ''}`;
            tab.textContent = this.formatCategoryName(category);
            tab.dataset.category = category;

            tab.addEventListener('click', () => {
                this.switchComponentCategory(category);
            });

            this.componentTabs.appendChild(tab);
        });

        // Add Raw Layers tab
        const rawLayersTab = document.createElement('button');
        rawLayersTab.className = `browser-tab ${this.isRawLayersMode ? 'active' : ''}`;
        rawLayersTab.textContent = 'Raw Layers';
        rawLayersTab.dataset.category = 'raw';

        rawLayersTab.addEventListener('click', () => {
            this.switchToRawLayersMode();
        });

        this.componentTabs.appendChild(rawLayersTab);
    }

    switchComponentCategory(category) {
        this.currentComponentCategory = category;
        this.isRawLayersMode = false;

        // Update tab states
        document.querySelectorAll('.browser-tab').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.category === category);
        });

        // Display components for this category
        this.displayComponentGrid(category);
    }

    switchToRawLayersMode() {
        this.isRawLayersMode = true;

        // Update tab states
        document.querySelectorAll('.browser-tab').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.category === 'raw');
        });

        // Display raw layers
        this.displayRawLayersGrid();
    }

    displayComponentGrid(category) {
        if (!this.componentBrowserContent) return;

        const components = this.allComponents[category] || [];

        if (components.length === 0) {
            this.componentBrowserContent.innerHTML = `
                <div style="text-align: center; padding: 40px; color: var(--text-muted);">
                    <i class="fas fa-info-circle" style="font-size: 2rem; margin-bottom: 10px;"></i>
                    <p>No components found in this category</p>
                </div>
            `;
            return;
        }

        const grid = document.createElement('div');
        grid.className = 'component-grid';

        components.forEach(component => {
            const componentElement = this.createComponentElement(component, category);
            grid.appendChild(componentElement);
        });

        this.componentBrowserContent.innerHTML = '';
        this.componentBrowserContent.appendChild(grid);
    }

    createComponentElement(component, category) {
        const element = document.createElement('div');
        element.className = 'component-item';
        element.dataset.componentName = component.name;
        element.dataset.category = category;

        // Create thumbnail
        const thumbnail = document.createElement('div');
        thumbnail.className = 'component-thumbnail loading';
        thumbnail.innerHTML = '<i class="fas fa-image"></i>';

        // Create content
        const content = document.createElement('div');
        content.className = 'component-content';

        const name = document.createElement('div');
        name.className = 'component-name';
        name.textContent = component.name;
        name.title = component.name; // Tooltip for long names

        const categoryBadge = document.createElement('div');
        categoryBadge.className = 'component-category';
        categoryBadge.textContent = category;

        content.appendChild(name);
        content.appendChild(categoryBadge);

        element.appendChild(thumbnail);
        element.appendChild(content);

        // Load component thumbnail
        this.loadComponentThumbnail(thumbnail, component.name);

        // Add click handler for selection
        element.addEventListener('click', (e) => this.handleComponentClick(e, component.name));

        // Add drag functionality if needed (for future enhancements)
        element.draggable = true;
        element.addEventListener('dragstart', (e) => this.handleComponentDragStart(e, component.name));

        return element;
    }

    async loadComponentThumbnail(thumbnailElement, componentName) {
        try {
            const previewUrl = `/api/preview/${this.currentJobId}/component/${encodeURIComponent(componentName)}`;

            const img = document.createElement('img');
            img.alt = componentName;

            img.onload = () => {
                thumbnailElement.replaceWith(img);
                img.className = 'component-thumbnail';
            };

            img.onerror = () => {
                thumbnailElement.className = 'component-thumbnail loading error';
                thumbnailElement.innerHTML = '<i class="fas fa-exclamation-triangle"></i>';
                thumbnailElement.title = 'Failed to load preview';
            };

            // Add cache busting for component thumbnails too
            const cacheBustUrl = `${previewUrl}?t=${Date.now()}`;
            img.src = cacheBustUrl;

        } catch (error) {
            console.error(`Error loading thumbnail for ${componentName}:`, error);
            thumbnailElement.className = 'component-thumbnail loading error';
            thumbnailElement.innerHTML = '<i class="fas fa-exclamation-triangle"></i>';
        }
    }

    handleComponentClick(e, componentName) {
        const element = e.currentTarget;

        // Toggle selection
        if (this.selectedComponents.has(componentName)) {
            this.selectedComponents.delete(componentName);
            element.classList.remove('selected');
        } else {
            this.selectedComponents.add(componentName);
            element.classList.add('selected');
        }

        this.updateSelectionInfo();
    }

    handleComponentDragStart(e, componentName) {
        e.dataTransfer.setData('text/plain', componentName);
        e.currentTarget.classList.add('dragging');
    }

    updateSelectionInfo() {
        // Could add selection counter or actions based on selected components
        console.log('Selected components:', Array.from(this.selectedComponents));
    }

    formatCategoryName(category) {
        return category.charAt(0).toUpperCase() + category.slice(1).replace(/_/g, ' ');
    }

    toggleLegacyMode() {
        if (this.isLegacyMode) {
            this.showComponentInterface();
        } else {
            this.showLegacyInterface();
        }
    }

    handleExtractionModeChange(e) {
        const isAllComponents = e.target.id === 'extract-all-components';
        const isExpressionsOnly = e.target.id === 'extract-expressions-only';

        if (e.target.checked) {
            if (isAllComponents) {
                this.extractExpressionsOnlyCheckbox.checked = false;
            } else if (isExpressionsOnly) {
                this.extractAllComponentsCheckbox.checked = false;
            }
        }
    }

    // Raw Layers Management
    async loadRawLayers() {
        try {
            const response = await fetch(`/api/raw-layers/${this.currentJobId}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            this.rawLayers = data.raw_layers || [];
            console.log('Raw layers loaded:', this.rawLayers.length);

        } catch (error) {
            console.error('Failed to load raw layers:', error);
            this.showStatusMessage(`Failed to load raw layers: ${error.message}`, 'error');
        }
    }

    displayRawLayersGrid() {
        if (!this.componentBrowserContent) return;

        if (this.rawLayers.length === 0) {
            this.componentBrowserContent.innerHTML = `
                <div style="text-align: center; padding: 40px; color: var(--text-muted);">
                    <i class="fas fa-info-circle" style="font-size: 2rem; margin-bottom: 10px;"></i>
                    <p>Loading raw layers...</p>
                </div>
            `;
            return;
        }

        const grid = document.createElement('div');
        grid.className = 'component-grid';

        this.rawLayers.forEach(layer => {
            // Only show actual layers, not groups
            if (layer.type === 'LAYER') {
                const layerElement = this.createRawLayerElement(layer);
                grid.appendChild(layerElement);
            }
        });

        this.componentBrowserContent.innerHTML = '';
        this.componentBrowserContent.appendChild(grid);
    }

    createRawLayerElement(layer) {
        const element = document.createElement('div');
        element.className = 'component-item';
        element.dataset.layerName = layer.name;
        element.dataset.category = 'raw';

        // Create thumbnail
        const thumbnail = document.createElement('div');
        thumbnail.className = 'component-thumbnail loading';
        thumbnail.innerHTML = '<i class="fas fa-layer-group"></i>';

        // Create content
        const content = document.createElement('div');
        content.className = 'component-content';

        const name = document.createElement('div');
        name.className = 'component-name';
        name.textContent = layer.name;
        name.title = layer.name; // Tooltip for long names

        const categoryBadge = document.createElement('div');
        categoryBadge.className = 'component-category';
        categoryBadge.textContent = 'raw layer';

        const dimensions = document.createElement('div');
        dimensions.className = 'component-dimensions';
        dimensions.style.fontSize = '0.7rem';
        dimensions.style.color = 'var(--text-muted)';
        if (layer.width && layer.height) {
            dimensions.textContent = `${layer.width}×${layer.height}`;
        }

        content.appendChild(name);
        content.appendChild(categoryBadge);
        if (dimensions.textContent) {
            content.appendChild(dimensions);
        }

        element.appendChild(thumbnail);
        element.appendChild(content);

        // Load raw layer thumbnail
        this.loadRawLayerThumbnail(thumbnail, layer.name);

        // Add click handler for selection
        element.addEventListener('click', (e) => this.handleComponentClick(e, layer.name));

        return element;
    }

    async loadRawLayerThumbnail(thumbnailElement, layerName) {
        try {
            // Use the raw-preview endpoint for isolated layer previews
            const previewUrl = `/api/raw-preview/${this.currentJobId}/${encodeURIComponent(layerName)}`;

            // Add timestamp for cache busting
            const cacheBustUrl = `${previewUrl}?t=${Date.now()}`;

            console.log(`🔍 Loading raw layer thumbnail for: "${layerName}"`);
            console.log(`📍 Preview URL: ${previewUrl}`);
            console.log(`🔄 Cache-busted URL: ${cacheBustUrl}`);
            console.log(`🆔 Job ID: ${this.currentJobId}`);

            const img = document.createElement('img');
            img.alt = layerName;

            img.onload = () => {
                thumbnailElement.innerHTML = ''; // Clear loading content
                thumbnailElement.appendChild(img);
                thumbnailElement.className = 'component-thumbnail';
                console.log(`✅ Raw layer thumbnail loaded successfully: ${layerName}`);
                console.log(`📏 Image dimensions: ${img.naturalWidth}x${img.naturalHeight}`);
            };

            img.onerror = async (event) => {
                thumbnailElement.className = 'component-thumbnail loading error';
                thumbnailElement.innerHTML = '<i class="fas fa-exclamation-triangle"></i>';
                thumbnailElement.title = 'Failed to load raw preview';
                console.error(`❌ Failed to load raw thumbnail for: ${layerName}`);
                console.error(`🔗 Failed URL: ${previewUrl}`);
                console.error(`🔄 Failed cache-busted URL: ${cacheBustUrl}`);
                console.error(`📊 Error event:`, event);

                // Try to get more detailed error information from the API
                try {
                    const response = await fetch(cacheBustUrl);
                    const statusText = response.statusText;
                    const status = response.status;
                    console.error(`🌐 HTTP Status: ${status} ${statusText}`);

                    if (!response.ok) {
                        const errorText = await response.text();
                        console.error(`📄 Error response body:`, errorText);
                    }
                } catch (fetchError) {
                    console.error(`🚫 Could not fetch error details:`, fetchError);
                }
            };

            img.src = cacheBustUrl;

        } catch (error) {
            console.error(`💥 Error loading raw layer thumbnail for ${layerName}:`, error);
            console.error(`🔍 Error stack:`, error.stack);
            thumbnailElement.className = 'component-thumbnail loading error';
            thumbnailElement.innerHTML = '<i class="fas fa-exclamation-triangle"></i>';
        }
    }

    // Expression Mapping (Legacy)
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

        // Create thumbnail element
        const thumbnail = document.createElement('div');
        thumbnail.className = 'expression-thumbnail loading';
        thumbnail.innerHTML = '<i class="fas fa-image"></i>';

        // Create content element
        const content = document.createElement('div');
        content.className = 'expression-content';

        const name = document.createElement('div');
        name.className = 'expression-name';
        name.textContent = expressionName;

        const meta = document.createElement('div');
        meta.className = 'expression-meta';
        meta.innerHTML = '<i class="fas fa-grip-vertical expression-icon"></i>Drag to category';

        content.appendChild(name);
        content.appendChild(meta);

        element.appendChild(thumbnail);
        element.appendChild(content);

        // Load thumbnail image
        this.loadExpressionThumbnail(thumbnail, expressionName);

        // Add drag event listeners
        element.addEventListener('dragstart', (e) => this.handleExpressionDragStart(e));
        element.addEventListener('dragend', (e) => this.handleExpressionDragEnd(e));

        return element;
    }

    async loadExpressionThumbnail(thumbnailElement, expressionName) {
        try {
            // Construct preview URL
            const previewUrl = `/api/preview/${this.currentJobId}/expression/${encodeURIComponent(expressionName)}`;

            // Create image element
            const img = document.createElement('img');
            img.className = 'expression-thumbnail';
            img.alt = expressionName;

            img.onload = () => {
                // Replace loading placeholder with actual image
                thumbnailElement.replaceWith(img);
                img.parentElement.classList.add('has-thumbnail');
            };

            img.onerror = () => {
                // Keep loading placeholder but update to error state
                thumbnailElement.className = 'expression-thumbnail loading error';
                thumbnailElement.innerHTML = '<i class="fas fa-exclamation-triangle"></i>';
                thumbnailElement.title = 'Failed to load preview';
            };

            // Load the image
            img.src = previewUrl;

        } catch (error) {
            console.error(`Error loading thumbnail for ${expressionName}:`, error);
            thumbnailElement.className = 'expression-thumbnail loading error';
            thumbnailElement.innerHTML = '<i class="fas fa-exclamation-triangle"></i>';
        }
    }

    // Drag and Drop for Mapping
    handleExpressionDragStart(e) {
        // Find the expression item element (in case drag started on a child element)
        const expressionItem = e.target.closest('.expression-item');
        if (expressionItem) {
            e.dataTransfer.setData('text/plain', expressionItem.dataset.expression);
            expressionItem.classList.add('dragging');
        }
    }

    handleExpressionDragEnd(e) {
        // Find the expression item element (in case drag ended on a child element)
        const expressionItem = e.target.closest('.expression-item');
        if (expressionItem) {
            expressionItem.classList.remove('dragging');
        }
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