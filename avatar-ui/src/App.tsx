import React, { useState, useCallback } from 'react';
import './App.css';
import './additional-styles.css';

// Slot palette configuration
const SLOT_PALETTE = {
  "Body": { "torso": {}, "arms": {}, "legs": {} },
  "Head": { "base": {}, "neck": {} },
  "Hair": { "back": {}, "mid": {}, "front": {}, "accessory": {} },
  "Eyes": {
    "EyeL": { "state": ["open","half","closed"] },
    "EyeR": { "state": ["open","half","closed"] },
    "IrisL": {}, "IrisR": {},
    "BrowL": { "shape": ["neutral","up","down","angry","sad"] },
    "BrowR": { "shape": ["neutral","up","down","angry","sad"] }
  },
  "Mouth": {
    "viseme": ["REST","AI","E","U","O","FV","L","WQ","MBP","SIL"],
    "emotion": ["neutral","smile","frown","angry","sad","joy"]
  },
  "Nose": { "base": {}, "shadow": {} },
  "Cheek": { "blush": {}, "shadow": {} },
  "Accessories": { "glasses": {}, "earrings": {}, "hats": {}, "masks": {} },
  "FX": { "sparkles": {}, "highlights": {} }
};

function App() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [slices, setSlices] = useState<any[]>([]);

  const handleFileUpload = useCallback(async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setIsProcessing(true);
      setError(null);

      try {
        // Simulate PSD processing
        await new Promise(resolve => setTimeout(resolve, 2000));

        // Mock slices data
        const mockSlices = [
          { id: '1', name: 'smile', path: 'Mouth/smile', width: 100, height: 50 },
          { id: '2', name: 'eyes_open', path: 'Eyes/open', width: 120, height: 60 },
          { id: '3', name: 'hair_front', path: 'Hair/front', width: 200, height: 300 },
        ];

        setSlices(mockSlices);
      } catch (err) {
        setError('Failed to process PSD file');
      } finally {
        setIsProcessing(false);
      }
    }
  }, []);

  const handleExport = useCallback(() => {
    alert('Export functionality would work here!');
  }, []);

  const generateSlotPaths = (config: any, prefix = ''): string[] => {
    const paths: string[] = [];

    Object.entries(config).forEach(([key, value]) => {
      const currentPath = prefix ? `${prefix}/${key}` : key;

      if (Array.isArray(value)) {
        value.forEach(item => paths.push(`${currentPath}/${item}`));
      } else if (typeof value === 'object' && value !== null && Object.keys(value).length > 0) {
        paths.push(...generateSlotPaths(value, currentPath));
      } else {
        paths.push(currentPath);
      }
    });

    return paths;
  };

  const allSlotPaths = generateSlotPaths(SLOT_PALETTE);

  return (
    <div className="app">
      <header className="app-header">
        <h1>Avatar Assembly UI - Clean Architecture</h1>
        <div className="header-controls">
          <input
            type="file"
            accept=".psd"
            onChange={handleFileUpload}
            className="file-input"
            id="psd-file-input"
          />
          <label htmlFor="psd-file-input" className="file-input-label">
            📁 Load PSD
          </label>

          {selectedFile && slices.length > 0 && (
            <button onClick={handleExport} className="export-button">
              📦 Export Bundle
            </button>
          )}
        </div>
      </header>

      {isProcessing && (
        <div className="loading-overlay">
          <div className="loading-spinner"></div>
          <div>Processing PSD...</div>
        </div>
      )}

      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
          <button onClick={() => setError(null)} style={{ marginLeft: '10px' }}>✕</button>
        </div>
      )}

      {slices.length > 0 ? (
        <main className="main-content">
          <div className="avatar-info">
            <h2>Avatar Information</h2>
            <div className="info-grid">
              <div>File: {selectedFile?.name}</div>
              <div>Total Slices: {slices.length}</div>
              <div>Size: {selectedFile ? Math.round(selectedFile.size / 1024) + ' KB' : 'Unknown'}</div>
            </div>
          </div>

          <div className="slices-section">
            <h3>Extracted Slices ({slices.length})</h3>
            <div className="slices-grid">
              {slices.map((slice) => (
                <div key={slice.id} className="slice-card">
                  <div className="slice-preview">
                    <div style={{
                      width: 64,
                      height: 64,
                      background: '#e9ecef',
                      border: '1px solid #dee2e6',
                      borderRadius: '4px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '12px',
                      color: '#6c757d'
                    }}>
                      {slice.name}
                    </div>
                  </div>
                  <div className="slice-info">
                    <div className="slice-name">{slice.name}</div>
                    <div className="slice-path">{slice.path}</div>
                    <div className="slice-size">{slice.width}×{slice.height}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="mapping-section">
            <h3>Available Slots</h3>
            <p>These are the canonical avatar slots available for mapping:</p>
            <div className="quick-slots">
              {allSlotPaths.slice(0, 20).map(slotPath => (
                <button
                  key={slotPath}
                  className="slot-button"
                >
                  {slotPath}
                </button>
              ))}
            </div>
          </div>
        </main>
      ) : (
        <div className="empty-state">
          <div className="empty-state-icon">🎨</div>
          <h2>Welcome to Avatar Assembly UI</h2>
          <p>Clean Architecture Implementation</p>
          {selectedFile ? (
            <p>Selected: {selectedFile.name} - Processing will begin when you upload...</p>
          ) : (
            <p>Upload a PSD file to get started extracting character expressions and building your avatar.</p>
          )}
          <label htmlFor="psd-file-input" className="file-input-label large">
            📁 Choose PSD File
          </label>
        </div>
      )}
    </div>
  );
}

export default App;