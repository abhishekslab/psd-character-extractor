import React, { useState, useCallback, useEffect } from 'react';
import UnmappedSlicesPanel from './components/UnmappedSlicesPanel';
import SlotPalette from './components/SlotPalette';
import SlotInspector from './components/SlotInspector';
import AvatarCanvas from './components/AvatarCanvas';
import { PSDProcessor } from './utils/psdLoader';
import { AutoMapper, MappingResult } from './utils/autoMapper';
import { BundleExporter } from './utils/bundleExporter';
import {
  ExtractedSlice,
  Avatar,
  SlotPalette as SlotPaletteType,
  PSDPathMapping,
  AutoMapRule
} from './types/avatar';
import slotPaletteConfig from './config/slot_palette.json';
import './App.css';

interface AppState {
  psdProcessor: PSDProcessor | null;
  allSlices: ExtractedSlice[];
  unmappedSlices: ExtractedSlice[];
  mappedSlices: Record<string, ExtractedSlice>;
  avatar: Avatar;
  selectedSlot: string | null;
  searchQuery: string;
  selectedSlices: ExtractedSlice[];
  visibilitySettings: Record<string, boolean>;
  zOffsets: Record<string, number>;
  tints: Record<string, string>;
  psdPathMappings: PSDPathMapping[];
  learnedRules: AutoMapRule[];
  isProcessing: boolean;
  error: string | null;
}

const DEFAULT_AVATAR: Avatar = {
  meta: {
    generator: 'psd-ce@1.0.0',
    rigId: 'anime-1024-headA-v1'
  },
  images: {
    slices: {}
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
    earL: { x: 450, y: 280 },
    earR: { x: 574, y: 280 }
  }
};

function App() {
  const [state, setState] = useState<AppState>({
    psdProcessor: null,
    allSlices: [],
    unmappedSlices: [],
    mappedSlices: {},
    avatar: DEFAULT_AVATAR,
    selectedSlot: null,
    searchQuery: '',
    selectedSlices: [],
    visibilitySettings: {},
    zOffsets: {},
    tints: {},
    psdPathMappings: [],
    learnedRules: [],
    isProcessing: false,
    error: null
  });

  // Initialize auto-mapper
  const [autoMapper] = useState(() => new AutoMapper(slotPaletteConfig as SlotPaletteType));

  const handleFileUpload = useCallback(async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setState(prev => ({ ...prev, isProcessing: true, error: null }));

    try {
      const processor = new PSDProcessor();
      await processor.loadPSD(file);

      const allSlices = await processor.extractAllSlices();
      const mappingResult = autoMapper.mapSlices(allSlices);

      // Create avatar with mapped slices
      const avatar = { ...DEFAULT_AVATAR };
      const mappedSlicesObj: Record<string, ExtractedSlice> = {};
      const psdPathMappings: PSDPathMapping[] = [];

      mappingResult.mapped.forEach(({ slice, canonicalSlot }) => {
        mappedSlicesObj[canonicalSlot] = slice;
        avatar.images.slices[canonicalSlot] = {
          x: slice.bounds.x,
          y: slice.bounds.y,
          w: slice.bounds.width,
          h: slice.bounds.height,
          id: slice.id
        };

        psdPathMappings.push({
          psdPath: slice.psdPath,
          sliceId: slice.id,
          canonical: canonicalSlot
        });
      });

      setState(prev => ({
        ...prev,
        psdProcessor: processor,
        allSlices,
        unmappedSlices: mappingResult.unmapped,
        mappedSlices: mappedSlicesObj,
        avatar,
        psdPathMappings,
        learnedRules: autoMapper.getPendingRules(),
        isProcessing: false
      }));

    } catch (error) {
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Unknown error occurred',
        isProcessing: false
      }));
    }
  }, [autoMapper]);

  const handleSliceSelect = useCallback((slice: ExtractedSlice) => {
    setState(prev => {
      const isSelected = prev.selectedSlices.some(s => s.id === slice.id);
      const newSelection = isSelected
        ? prev.selectedSlices.filter(s => s.id !== slice.id)
        : [...prev.selectedSlices, slice];

      return { ...prev, selectedSlices: newSelection };
    });
  }, []);

  const handleSlotSelect = useCallback((slotPath: string) => {
    setState(prev => ({ ...prev, selectedSlot: slotPath }));
  }, []);

  const handleSlotDrop = useCallback((slotPath: string, slice: ExtractedSlice) => {
    // Find the actual slice from unmapped slices
    const actualSlice = state.unmappedSlices.find(s => s.id === slice.id);
    if (!actualSlice) return;

    // Map the slice manually
    autoMapper.manualMap(actualSlice, slotPath);

    setState(prev => {
      const newMappedSlices = { ...prev.mappedSlices };
      newMappedSlices[slotPath] = actualSlice;

      const newUnmappedSlices = prev.unmappedSlices.filter(s => s.id !== actualSlice.id);

      const newAvatar = { ...prev.avatar };
      newAvatar.images.slices[slotPath] = {
        x: actualSlice.bounds.x,
        y: actualSlice.bounds.y,
        w: actualSlice.bounds.width,
        h: actualSlice.bounds.height,
        id: actualSlice.id
      };

      const newPsdPathMappings = [...prev.psdPathMappings, {
        psdPath: actualSlice.psdPath,
        sliceId: actualSlice.id,
        canonical: slotPath
      }];

      return {
        ...prev,
        mappedSlices: newMappedSlices,
        unmappedSlices: newUnmappedSlices,
        avatar: newAvatar,
        psdPathMappings: newPsdPathMappings,
        learnedRules: autoMapper.getPendingRules(),
        selectedSlot: slotPath
      };
    });
  }, [state.unmappedSlices, autoMapper]);

  const handleRemoveSlice = useCallback((slotPath: string) => {
    setState(prev => {
      const slice = prev.mappedSlices[slotPath];
      if (!slice) return prev;

      const newMappedSlices = { ...prev.mappedSlices };
      delete newMappedSlices[slotPath];

      const newUnmappedSlices = [...prev.unmappedSlices, slice];

      const newAvatar = { ...prev.avatar };
      delete newAvatar.images.slices[slotPath];

      const newPsdPathMappings = prev.psdPathMappings.filter(
        mapping => mapping.canonical !== slotPath
      );

      slice.mapped = false;
      slice.canonicalSlot = undefined;

      return {
        ...prev,
        mappedSlices: newMappedSlices,
        unmappedSlices: newUnmappedSlices,
        avatar: newAvatar,
        psdPathMappings: newPsdPathMappings,
        selectedSlot: null
      };
    });
  }, []);

  const handleReplaceSlice = useCallback((slotPath: string) => {
    // This would open a file picker or slice selector
    // For now, just log the action
    console.log('Replace slice for slot:', slotPath);
  }, []);

  const handleNudgeZ = useCallback((slotPath: string, offset: number) => {
    setState(prev => ({
      ...prev,
      zOffsets: { ...prev.zOffsets, [slotPath]: offset }
    }));
  }, []);

  const handleTint = useCallback((slotPath: string, tint: string) => {
    setState(prev => ({
      ...prev,
      tints: { ...prev.tints, [slotPath]: tint }
    }));
  }, []);

  const handleToggleVisibility = useCallback((partName: string, visible: boolean) => {
    setState(prev => ({
      ...prev,
      visibilitySettings: { ...prev.visibilitySettings, [partName]: visible }
    }));
  }, []);

  const handleSearch = useCallback((query: string) => {
    setState(prev => ({ ...prev, searchQuery: query }));
  }, []);

  const handleExportBundle = useCallback(async () => {
    try {
      const bundleName = 'Character_Avatar';
      const exporter = new BundleExporter(
        state.avatar,
        state.mappedSlices,
        state.psdPathMappings,
        [], // No wardrobe items for now
        { aliases: state.learnedRules }
      );

      await exporter.exportBundle(bundleName, {
        includeAtlas: true,
        includeRawSlices: true,
        compressionLevel: 6,
        generatePreviews: true
      });

    } catch (error) {
      console.error('Export failed:', error);
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Export failed'
      }));
    }
  }, [state.avatar, state.mappedSlices, state.psdPathMappings, state.learnedRules]);

  return (
    <div className="app">
      <header className="app-header">
        <h1>Avatar Assembly UI</h1>
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

          {Object.keys(state.mappedSlices).length > 0 && (
            <button
              onClick={handleExportBundle}
              className="export-button"
            >
              📦 Export Bundle
            </button>
          )}
        </div>
      </header>

      {state.isProcessing && (
        <div className="loading-overlay">
          <div className="loading-spinner"></div>
          <div>Processing PSD...</div>
        </div>
      )}

      {state.error && (
        <div className="error-message">
          <strong>Error:</strong> {state.error}
        </div>
      )}

      {state.allSlices.length > 0 && (
        <main className="app-main">
          <div className="left-panel">
            <UnmappedSlicesPanel
              slices={state.unmappedSlices}
              onSliceSelect={handleSliceSelect}
              selectedSlices={state.selectedSlices}
              onSearch={handleSearch}
              searchQuery={state.searchQuery}
            />
          </div>

          <div className="center-panel">
            <AvatarCanvas
              mappedSlices={state.mappedSlices}
              avatar={state.avatar}
              onSliceSelect={handleSlotSelect}
              selectedSlot={state.selectedSlot}
              visibilitySettings={state.visibilitySettings}
              onToggleVisibility={handleToggleVisibility}
              showAnchors={state.visibilitySettings['__anchors'] || false}
              showFitBoxes={state.visibilitySettings['__fitboxes'] || false}
              zOffsets={state.zOffsets}
              tints={state.tints}
            />
          </div>

          <div className="right-panel">
            <div className="right-panel-top">
              <SlotPalette
                slotPalette={slotPaletteConfig as SlotPaletteType}
                mappedSlices={state.mappedSlices}
                onSlotSelect={handleSlotSelect}
                selectedSlot={state.selectedSlot}
                onSlotDrop={handleSlotDrop}
              />
            </div>

            <div className="right-panel-bottom">
              <SlotInspector
                selectedSlot={state.selectedSlot}
                slice={state.selectedSlot ? state.mappedSlices[state.selectedSlot] || null : null}
                onRemoveSlice={handleRemoveSlice}
                onReplaceSlice={handleReplaceSlice}
                onNudgeZ={handleNudgeZ}
                onTint={handleTint}
                zOffset={state.selectedSlot ? state.zOffsets[state.selectedSlot] || 0 : 0}
                tint={state.selectedSlot ? state.tints[state.selectedSlot] || '#ffffff' : '#ffffff'}
              />
            </div>
          </div>
        </main>
      )}

      {state.allSlices.length === 0 && !state.isProcessing && (
        <div className="empty-state">
          <div className="empty-state-icon">🎨</div>
          <h2>Welcome to Avatar Assembly UI</h2>
          <p>Upload a PSD file to get started extracting character expressions and building your avatar.</p>
          <label htmlFor="psd-file-input" className="file-input-label large">
            📁 Choose PSD File
          </label>
        </div>
      )}
    </div>
  );
}

export default App;