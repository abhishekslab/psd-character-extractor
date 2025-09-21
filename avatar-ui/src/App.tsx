import React, { useCallback, useState } from 'react';
import { useAvatarAssembly } from './presentation/hooks/useAvatarAssembly';
import AvatarCanvas from './components/AvatarCanvas';
import UnmappedSlicesPanel from './components/UnmappedSlicesPanel';
import SlotPalette from './components/SlotPalette';
import type { ExtractedSlice, SlotPalette as SlotPaletteType } from './types/avatar';
import './App.css';
import './additional-styles.css';

// Slot palette configuration
const SLOT_PALETTE: SlotPaletteType = {
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
  // Clean Architecture - use the presentation layer hook
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

  // UI-specific state (not business logic)
  const [selectedSlices, setSelectedSlices] = useState<ExtractedSlice[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [visibilitySettings, setVisibilitySettings] = useState<Record<string, boolean>>({});
  const [zOffsets] = useState<Record<string, number>>({});
  const [tints] = useState<Record<string, string>>({});
  const [showAnchors, setShowAnchors] = useState(false);
  const [showFitBoxes, setShowFitBoxes] = useState(false);

  // Convert domain entities to UI types for compatibility with existing components
  const convertSliceForUI = useCallback((slice: any): ExtractedSlice => {
    return {
      id: slice.id.value,
      name: slice.name,
      psdPath: slice.layerPath.value,
      image: slice.imageData || new ImageData(1, 1), // Fallback
      canvas: slice.canvas,
      bounds: {
        x: slice.bounds.x,
        y: slice.bounds.y,
        width: slice.bounds.width,
        height: slice.bounds.height
      },
      mapped: slice.canonicalSlot !== undefined,
      canonicalSlot: slice.canonicalSlot
    };
  }, []);

  const convertAvatarForUI = useCallback((avatar: any) => {
    if (!avatar) return null;

    return {
      meta: {
        generator: 'psd-ce@1.0.0',
        rigId: avatar.rigId.value
      },
      images: {
        slices: {} // Will be populated from mapped slices
      },
      drawOrder: [
        'Body/*',
        'Head/*',
        'Hair/back',
        'Eyes/*',
        'Brows/*',
        'Mouth/*',
        'Nose/*',
        'Cheek/*',
        'Hair/front',
        'Accessories/*',
        'FX/*'
      ],
      anchors: {
        headPivot: { x: 512, y: 256 },
        mouthCenter: { x: 520, y: 320 },
        neckBase: { x: 512, y: 400 },
        earL: { x: 460, y: 280 },
        earR: { x: 564, y: 280 }
      }
    };
  }, []);

  // Convert domain slices to UI format
  const uiUnmappedSlices = unmappedSlices.map(convertSliceForUI);
  const uiMappedSlicesArray = mappedSlices.map(convertSliceForUI);
  const uiMappedSlices: Record<string, ExtractedSlice> = {};

  uiMappedSlicesArray.forEach(slice => {
    if (slice.canonicalSlot) {
      uiMappedSlices[slice.canonicalSlot] = slice;
    }
  });

  const uiAvatar = convertAvatarForUI(avatar);

  // Event handlers
  const handleFileUpload = useCallback(async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      await loadPSD(file);
    }
  }, [loadPSD]);

  const handleSliceSelect = useCallback((slice: ExtractedSlice) => {
    setSelectedSlices(prev => {
      const isSelected = prev.some(s => s.id === slice.id);
      if (isSelected) {
        return prev.filter(s => s.id !== slice.id);
      } else {
        return [...prev, slice];
      }
    });
  }, []);

  const handleSlotDrop = useCallback(async (slotPath: string, droppedSlice: ExtractedSlice) => {
    await mapSliceToSlot(droppedSlice.id, slotPath);
    setSelectedSlices(prev => prev.filter(s => s.id !== droppedSlice.id));
  }, [mapSliceToSlot]);

  const handleCanvasSliceSelect = useCallback((slotPath: string) => {
    selectSlot(slotPath);
  }, [selectSlot]);

  const handleToggleVisibility = useCallback((partName: string, visible: boolean) => {
    if (partName === '__anchors') {
      setShowAnchors(visible);
    } else if (partName === '__fitboxes') {
      setShowFitBoxes(visible);
    } else {
      setVisibilitySettings(prev => ({
        ...prev,
        [partName]: visible
      }));
    }
  }, []);

  const handleExport = useCallback(async () => {
    if (mappedSlices.length === 0) {
      alert('Please map some slices before exporting.');
      return;
    }
    await exportBundle('Character_Avatar');
    alert('Bundle exported successfully!');
  }, [mappedSlices.length, exportBundle]);

  return (
    <div className="app">
      <header className="app-header">
        <h1>Avatar Assembly UI - Complete Implementation</h1>
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
          <div>Processing PSD file...</div>
          <div className="loading-details">
            Extracting layers and generating slices...
          </div>
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

          <div className="workspace">
            <div className="left-panel">
              <UnmappedSlicesPanel
                slices={uiUnmappedSlices}
                onSliceSelect={handleSliceSelect}
                selectedSlices={selectedSlices}
                onSearch={setSearchQuery}
                searchQuery={searchQuery}
              />
            </div>

            <div className="center-panel">
              {uiAvatar && (
                <AvatarCanvas
                  mappedSlices={uiMappedSlices}
                  avatar={uiAvatar}
                  onSliceSelect={handleCanvasSliceSelect}
                  selectedSlot={selectedSlot}
                  visibilitySettings={visibilitySettings}
                  onToggleVisibility={handleToggleVisibility}
                  showAnchors={showAnchors}
                  showFitBoxes={showFitBoxes}
                  zOffsets={zOffsets}
                  tints={tints}
                />
              )}
            </div>

            <div className="right-panel">
              <SlotPalette
                palette={SLOT_PALETTE}
                mappedSlices={uiMappedSlices}
                onSlotDrop={handleSlotDrop}
                selectedSlot={selectedSlot}
                onSlotSelect={selectSlot}
              />
            </div>
          </div>
        </main>
      ) : (
        <div className="empty-state">
          <div className="empty-state-icon">🎨</div>
          <h2>Welcome to Avatar Assembly UI</h2>
          <p>Complete Clean Architecture Implementation</p>
          <p>Upload a PSD file to extract character expressions and build your avatar bundle.</p>
          <div className="features-list">
            <div className="feature-item">✅ Clean Architecture with Domain-Driven Design</div>
            <div className="feature-item">✅ Real PSD.js integration</div>
            <div className="feature-item">✅ PixiJS canvas rendering</div>
            <div className="feature-item">✅ Drag-and-drop slice mapping</div>
            <div className="feature-item">✅ Complete ZIP bundle export</div>
          </div>
          <label htmlFor="psd-file-input" className="file-input-label large">
            📁 Choose PSD File
          </label>
        </div>
      )}

      <style>{`
        .workspace {
          display: grid;
          grid-template-columns: 1fr 2fr 1fr;
          gap: 24px;
          height: calc(100vh - 300px);
          min-height: 600px;
        }

        .left-panel,
        .right-panel {
          display: flex;
          flex-direction: column;
        }

        .center-panel {
          background: white;
          border-radius: 8px;
          overflow: hidden;
        }

        .loading-details {
          font-size: 14px;
          color: #6c757d;
          margin-top: 8px;
        }

        .features-list {
          display: inline-block;
          text-align: left;
          margin: 24px 0;
        }

        .feature-item {
          margin: 8px 0;
          font-size: 14px;
          color: #28a745;
        }

        @media (max-width: 1200px) {
          .workspace {
            grid-template-columns: 1fr;
            grid-template-rows: auto auto auto;
          }

          .center-panel {
            order: 1;
          }

          .left-panel {
            order: 2;
          }

          .right-panel {
            order: 3;
          }
        }
      `}</style>
    </div>
  );
}

export default App;