import React, { useRef, useEffect, useState, useCallback } from 'react';
import * as PIXI from 'pixi.js';
import { ExtractedSlice, Avatar } from '../types/avatar';

interface AvatarCanvasProps {
  mappedSlices: Record<string, ExtractedSlice>;
  avatar: Avatar;
  onSliceSelect: (slotPath: string) => void;
  selectedSlot: string | null;
  visibilitySettings: Record<string, boolean>;
  onToggleVisibility: (partName: string, visible: boolean) => void;
  showAnchors: boolean;
  showFitBoxes: boolean;
  zOffsets: Record<string, number>;
  tints: Record<string, string>;
}

interface PixiSliceSprite extends PIXI.Sprite {
  slotPath?: string;
  originalTexture?: PIXI.Texture;
}

const AvatarCanvas: React.FC<AvatarCanvasProps> = ({
  mappedSlices,
  avatar,
  onSliceSelect,
  selectedSlot,
  visibilitySettings,
  onToggleVisibility,
  showAnchors,
  showFitBoxes,
  zOffsets,
  tints
}) => {
  const canvasRef = useRef<HTMLDivElement>(null);
  const pixiAppRef = useRef<PIXI.Application | null>(null);
  const spritesRef = useRef<Map<string, PixiSliceSprite>>(new Map());
  const anchorsRef = useRef<PIXI.Container | null>(null);
  const fitBoxesRef = useRef<PIXI.Container | null>(null);
  const [isInitialized, setIsInitialized] = useState(false);

  // Initialize PIXI application
  useEffect(() => {
    if (!canvasRef.current || isInitialized) return;

    const initPixi = async () => {
      try {
        const app = new PIXI.Application();
        await app.init({
          width: 1024,
          height: 1024,
          backgroundColor: 0xf8f9fa,
          antialias: true,
          resolution: window.devicePixelRatio || 1,
          autoDensity: true
        });

        if (canvasRef.current) {
          canvasRef.current.appendChild(app.canvas);
        }

        // Create containers for different layers
        const mainContainer = new PIXI.Container();
        const anchorsContainer = new PIXI.Container();
        const fitBoxesContainer = new PIXI.Container();

        app.stage.addChild(mainContainer);
        app.stage.addChild(anchorsContainer);
        app.stage.addChild(fitBoxesContainer);

        pixiAppRef.current = app;
        anchorsRef.current = anchorsContainer;
        fitBoxesRef.current = fitBoxesContainer;

        // Add interaction
        app.stage.interactive = true;
        app.stage.on('pointerdown', handleCanvasClick);

        setIsInitialized(true);
      } catch (error) {
        console.error('Failed to initialize PIXI:', error);
      }
    };

    initPixi();

    return () => {
      if (pixiAppRef.current) {
        pixiAppRef.current.destroy(true);
        pixiAppRef.current = null;
      }
      setIsInitialized(false);
    };
  }, []);

  const handleCanvasClick = useCallback((event: PIXI.FederatedPointerEvent) => {
    if (!pixiAppRef.current) return;

    const point = event.global;
    let foundSprite: PixiSliceSprite | null = null;

    // Find the topmost sprite at the click position
    spritesRef.current.forEach((sprite) => {
      if (sprite.visible && sprite.containsPoint(point)) {
        if (!foundSprite || sprite.zIndex > foundSprite.zIndex) {
          foundSprite = sprite;
        }
      }
    });

    if (foundSprite && foundSprite.slotPath) {
      onSliceSelect(foundSprite.slotPath);
    }
  }, [onSliceSelect]);

  // Create texture from canvas
  const createTextureFromCanvas = useCallback((canvas: HTMLCanvasElement): PIXI.Texture => {
    if (!pixiAppRef.current) throw new Error('PIXI not initialized');

    const baseTexture = PIXI.BaseTexture.from(canvas);
    return new PIXI.Texture(baseTexture);
  }, []);

  // Apply tint to sprite
  const applyTint = useCallback((sprite: PixiSliceSprite, tintColor: string) => {
    if (!sprite.originalTexture) {
      sprite.originalTexture = sprite.texture;
    }

    if (tintColor && tintColor !== '#ffffff') {
      // Convert hex to PIXI color
      const hexColor = tintColor.replace('#', '');
      const tintValue = parseInt(hexColor, 16);
      sprite.tint = tintValue;
    } else {
      sprite.tint = 0xffffff; // White (no tint)
    }
  }, []);

  // Create or update sprite for a slice
  const createOrUpdateSprite = useCallback((slotPath: string, slice: ExtractedSlice) => {
    if (!pixiAppRef.current) return;

    let sprite = spritesRef.current.get(slotPath);

    if (!sprite) {
      // Create new sprite
      const texture = createTextureFromCanvas(slice.canvas);
      sprite = new PIXI.Sprite(texture) as PixiSliceSprite;
      sprite.slotPath = slotPath;
      sprite.originalTexture = texture;
      sprite.interactive = true;
      sprite.cursor = 'pointer';

      pixiAppRef.current.stage.addChild(sprite);
      spritesRef.current.set(slotPath, sprite);
    } else {
      // Update existing sprite
      const texture = createTextureFromCanvas(slice.canvas);
      sprite.texture = texture;
      sprite.originalTexture = texture;
    }

    // Set position
    sprite.x = slice.bounds.x;
    sprite.y = slice.bounds.y;

    // Apply z-index from draw order and offset
    const baseZIndex = avatar.drawOrder.findIndex(pattern => {
      if (pattern.includes('*')) {
        const prefix = pattern.replace('/*', '');
        return slotPath.startsWith(prefix);
      }
      return slotPath === pattern;
    });

    const zOffset = zOffsets[slotPath] || 0;
    sprite.zIndex = (baseZIndex * 10) + zOffset;

    // Apply tint
    const tint = tints[slotPath] || '#ffffff';
    applyTint(sprite, tint);

    // Set visibility based on part visibility
    const partName = slotPath.split('/')[0];
    const isPartVisible = visibilitySettings[partName] !== false;
    sprite.visible = isPartVisible;

    // Highlight if selected
    if (slotPath === selectedSlot) {
      sprite.alpha = 1.0;
      // Add selection outline effect
      const graphics = new PIXI.Graphics();
      graphics.lineStyle(2, 0x007bff, 1);
      graphics.drawRect(0, 0, sprite.width, sprite.height);
      sprite.addChild(graphics);
    } else {
      sprite.alpha = 1.0;
      // Remove any existing selection graphics
      sprite.children.forEach(child => {
        if (child instanceof PIXI.Graphics) {
          sprite.removeChild(child);
        }
      });
    }
  }, [avatar.drawOrder, zOffsets, tints, visibilitySettings, selectedSlot, createTextureFromCanvas, applyTint]);

  // Remove sprite
  const removeSprite = useCallback((slotPath: string) => {
    if (!pixiAppRef.current) return;

    const sprite = spritesRef.current.get(slotPath);
    if (sprite) {
      pixiAppRef.current.stage.removeChild(sprite);
      sprite.destroy();
      spritesRef.current.delete(slotPath);
    }
  }, []);

  // Update all sprites
  useEffect(() => {
    if (!isInitialized || !pixiAppRef.current) return;

    // Remove sprites that no longer exist
    const currentSlotPaths = new Set(Object.keys(mappedSlices));
    spritesRef.current.forEach((sprite, slotPath) => {
      if (!currentSlotPaths.has(slotPath)) {
        removeSprite(slotPath);
      }
    });

    // Create or update sprites for current slices
    Object.entries(mappedSlices).forEach(([slotPath, slice]) => {
      createOrUpdateSprite(slotPath, slice);
    });

    // Sort sprites by z-index
    if (pixiAppRef.current.stage.children.length > 0) {
      pixiAppRef.current.stage.children.sort((a, b) => (a.zIndex || 0) - (b.zIndex || 0));
    }
  }, [mappedSlices, isInitialized, createOrUpdateSprite, removeSprite]);

  // Update sprite properties when settings change
  useEffect(() => {
    if (!isInitialized) return;

    spritesRef.current.forEach((sprite, slotPath) => {
      const slice = mappedSlices[slotPath];
      if (slice) {
        createOrUpdateSprite(slotPath, slice);
      }
    });
  }, [visibilitySettings, selectedSlot, zOffsets, tints, isInitialized, mappedSlices, createOrUpdateSprite]);

  // Draw anchors
  const drawAnchors = useCallback(() => {
    if (!anchorsRef.current || !avatar.anchors) return;

    anchorsRef.current.removeChildren();

    if (!showAnchors) return;

    Object.entries(avatar.anchors).forEach(([name, point]) => {
      const graphics = new PIXI.Graphics();

      // Draw anchor point
      graphics.beginFill(0xff6b6b);
      graphics.drawCircle(point.x, point.y, 4);
      graphics.endFill();

      // Draw crosshair
      graphics.lineStyle(1, 0xff6b6b);
      graphics.moveTo(point.x - 8, point.y);
      graphics.lineTo(point.x + 8, point.y);
      graphics.moveTo(point.x, point.y - 8);
      graphics.lineTo(point.x, point.y + 8);

      // Add label
      const text = new PIXI.Text(name, {
        fontSize: 10,
        fill: 0xff6b6b,
        fontWeight: 'bold'
      });
      text.x = point.x + 8;
      text.y = point.y - 8;

      anchorsRef.current!.addChild(graphics);
      anchorsRef.current!.addChild(text);
    });
  }, [avatar.anchors, showAnchors]);

  // Draw fit boxes (if available)
  const drawFitBoxes = useCallback(() => {
    if (!fitBoxesRef.current) return;

    fitBoxesRef.current.removeChildren();

    if (!showFitBoxes) return;

    // This would require fit box data from manifest
    // For now, just show a placeholder implementation
    const sampleFitBoxes = {
      hair: { x: 280, y: 40, w: 460, h: 520 },
      top: { x: 240, y: 380, w: 520, h: 420 }
    };

    Object.entries(sampleFitBoxes).forEach(([type, box]) => {
      const graphics = new PIXI.Graphics();
      graphics.lineStyle(2, 0x28a745, 0.8);
      graphics.drawRect(box.x, box.y, box.w, box.h);

      const text = new PIXI.Text(`${type} fit box`, {
        fontSize: 12,
        fill: 0x28a745,
        fontWeight: 'bold'
      });
      text.x = box.x + 4;
      text.y = box.y + 4;

      fitBoxesRef.current!.addChild(graphics);
      fitBoxesRef.current!.addChild(text);
    });
  }, [showFitBoxes]);

  // Update overlays when settings change
  useEffect(() => {
    drawAnchors();
    drawFitBoxes();
  }, [showAnchors, showFitBoxes, drawAnchors, drawFitBoxes]);

  const getVisibilityControls = () => {
    const parts = ['Body', 'Head', 'Hair', 'Eyes', 'Mouth', 'Nose', 'Cheek', 'Accessories', 'FX'];
    return parts.map(part => (
      <div key={part} className="visibility-control">
        <label>
          <input
            type="checkbox"
            checked={visibilitySettings[part] !== false}
            onChange={(e) => onToggleVisibility(part, e.target.checked)}
          />
          {part}
        </label>
      </div>
    ));
  };

  return (
    <div className="avatar-canvas-container">
      <div className="canvas-header">
        <h3>Avatar Preview</h3>
        <div className="canvas-controls">
          <button
            className={`control-button ${showAnchors ? 'active' : ''}`}
            onClick={() => onToggleVisibility('__anchors', !showAnchors)}
            title="Show anchor points"
          >
            📍 Anchors
          </button>
          <button
            className={`control-button ${showFitBoxes ? 'active' : ''}`}
            onClick={() => onToggleVisibility('__fitboxes', !showFitBoxes)}
            title="Show fit boxes"
          >
            📦 Fit Boxes
          </button>
        </div>
      </div>

      <div className="canvas-wrapper">
        <div ref={canvasRef} className="pixi-canvas" />
      </div>

      <div className="visibility-panel">
        <h4>Part Visibility</h4>
        <div className="visibility-controls">
          {getVisibilityControls()}
        </div>
      </div>

      <style jsx>{`
        .avatar-canvas-container {
          background: white;
          border: 1px solid #dee2e6;
          border-radius: 8px;
          padding: 16px;
          height: 100%;
          display: flex;
          flex-direction: column;
        }

        .canvas-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
          border-bottom: 1px solid #e9ecef;
          padding-bottom: 12px;
        }

        .canvas-header h3 {
          margin: 0;
          color: #495057;
          font-size: 16px;
          font-weight: 600;
        }

        .canvas-controls {
          display: flex;
          gap: 8px;
        }

        .control-button {
          padding: 6px 12px;
          border: 1px solid #ced4da;
          background: white;
          border-radius: 4px;
          cursor: pointer;
          font-size: 12px;
          transition: all 0.2s ease;
        }

        .control-button:hover {
          background: #f8f9fa;
          border-color: #adb5bd;
        }

        .control-button.active {
          background: #007bff;
          color: white;
          border-color: #007bff;
        }

        .canvas-wrapper {
          flex: 1;
          display: flex;
          justify-content: center;
          align-items: center;
          background: #f8f9fa;
          border: 2px dashed #dee2e6;
          border-radius: 8px;
          margin-bottom: 16px;
          overflow: hidden;
          position: relative;
        }

        .pixi-canvas {
          max-width: 100%;
          max-height: 100%;
        }

        .pixi-canvas :global(canvas) {
          max-width: 100%;
          max-height: 100%;
          object-fit: contain;
          border-radius: 4px;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }

        .visibility-panel {
          margin-top: auto;
        }

        .visibility-panel h4 {
          margin: 0 0 8px 0;
          color: #495057;
          font-size: 14px;
          font-weight: 600;
        }

        .visibility-controls {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(80px, 1fr));
          gap: 8px;
        }

        .visibility-control {
          display: flex;
          align-items: center;
        }

        .visibility-control label {
          display: flex;
          align-items: center;
          font-size: 12px;
          color: #495057;
          cursor: pointer;
          user-select: none;
        }

        .visibility-control input {
          margin-right: 6px;
        }
      `}</style>
    </div>
  );
};

export default AvatarCanvas;