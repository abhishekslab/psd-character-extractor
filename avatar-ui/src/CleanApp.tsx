import React, { useCallback } from 'react';
import { useAvatarAssembly } from './presentation/hooks/useAvatarAssembly';
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

function CleanApp() {
  const {
    avatar,
    allSlices,
    unmappedSlices,
    mappedSlices,
    selectedSlot,
    isProcessing,
    error,
    loadPSD,
    mapSliceToSlot,
    exportBundle,
    selectSlot,
    clearError
  } = useAvatarAssembly();

  const handleFileUpload = useCallback(async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      await loadPSD(file);
    }
  }, [loadPSD]);

  const handleSliceClick = useCallback((slice: any, slotPath: string) => {
    mapSliceToSlot(slice.id.value, slotPath);
  }, [mapSliceToSlot]);

  const handleExport = useCallback(() => {
    exportBundle('Character_Avatar');
  }, [exportBundle]);

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

          {avatar && mappedSlices.length > 0 && (
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
          <button onClick={clearError} style={{ marginLeft: '10px' }}>✕</button>
        </div>
      )}

      {allSlices.length > 0 ? (
        <main className="main-content">
          <div className="avatar-info">
            <h2>Avatar Information</h2>
            {avatar && (
              <div className="info-grid">
                <div>Rig ID: {avatar.rigId.value}</div>
                <div>Total Slices: {allSlices.length}</div>
                <div>Mapped: {mappedSlices.length}</div>
                <div>Unmapped: {unmappedSlices.length}</div>
              </div>
            )}
          </div>

          <div className="slices-section">
            <h3>Unmapped Slices ({unmappedSlices.length})</h3>
            <div className="slices-grid">
              {unmappedSlices.map((slice) => (
                <div key={slice.id.value} className="slice-card">
                  <div className="slice-preview">
                    <canvas
                      ref={(canvas) => {
                        if (canvas && slice.canvas) {
                          canvas.width = 64;
                          canvas.height = 64;
                          const ctx = canvas.getContext('2d');
                          if (ctx) {
                            ctx.drawImage(
                              slice.canvas,
                              0, 0, slice.canvas.width, slice.canvas.height,
                              0, 0, 64, 64
                            );
                          }
                        }
                      }}
                      width={64}
                      height={64}
                    />
                  </div>
                  <div className="slice-info">
                    <div className="slice-name">{slice.name}</div>
                    <div className="slice-path">{slice.layerPath.value}</div>
                    <div className="slice-size">{slice.bounds.width}×{slice.bounds.height}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="mapping-section">
            <h3>Quick Mapping</h3>
            <p>Click a slot below, then click an unmapped slice to map it:</p>
            <div className="quick-slots">
              {allSlotPaths.slice(0, 20).map(slotPath => (
                <button
                  key={slotPath}
                  className={`slot-button ${selectedSlot === slotPath ? 'selected' : ''}`}
                  onClick={() => selectSlot(slotPath)}
                >
                  {slotPath}
                </button>
              ))}
            </div>

            {selectedSlot && (
              <div className="mapping-helper">
                <h4>Selected Slot: {selectedSlot}</h4>
                <p>Click an unmapped slice above to assign it to this slot.</p>
                <div className="unmapped-for-mapping">
                  {unmappedSlices.slice(0, 5).map((slice) => (
                    <button
                      key={slice.id.value}
                      className="slice-mapping-button"
                      onClick={() => handleSliceClick(slice, selectedSlot)}
                    >
                      Map "{slice.name}"
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="mapped-section">
            <h3>Mapped Slices ({mappedSlices.length})</h3>
            <div className="mapped-grid">
              {mappedSlices.map((slice) => (
                <div key={slice.id.value} className="mapped-slice">
                  <div className="mapped-preview">
                    <canvas
                      ref={(canvas) => {
                        if (canvas && slice.canvas) {
                          canvas.width = 48;
                          canvas.height = 48;
                          const ctx = canvas.getContext('2d');
                          if (ctx) {
                            ctx.drawImage(
                              slice.canvas,
                              0, 0, slice.canvas.width, slice.canvas.height,
                              0, 0, 48, 48
                            );
                          }
                        }
                      }}
                      width={48}
                      height={48}
                    />
                  </div>
                  <div className="mapped-info">
                    <div className="mapped-name">{slice.name}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </main>
      ) : (
        <div className="empty-state">
          <div className="empty-state-icon">🎨</div>
          <h2>Welcome to Avatar Assembly UI</h2>
          <p>Clean Architecture Implementation</p>
          <p>Upload a PSD file to get started extracting character expressions and building your avatar.</p>
          <label htmlFor="psd-file-input" className="file-input-label large">
            📁 Choose PSD File
          </label>
        </div>
      )}
    </div>
  );
}

export default CleanApp;