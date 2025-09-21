import React, { useState, useCallback } from 'react';
import type { SlotPalette as SlotPaletteType, ExtractedSlice } from '../types/avatar';

interface SlotPaletteProps {
  palette: SlotPaletteType;
  mappedSlices: Record<string, ExtractedSlice>;
  onSlotSelect: (slotPath: string) => void;
  selectedSlot: string | null;
  onSlotDrop: (slotPath: string, slice: ExtractedSlice) => void;
}

interface SlotDropEvent {
  slotPath: string;
  slice: ExtractedSlice;
}

const SlotPalette: React.FC<SlotPaletteProps> = ({
  palette,
  mappedSlices,
  onSlotSelect,
  selectedSlot,
  onSlotDrop
}) => {
  const [expandedParts, setExpandedParts] = useState<Set<string>>(new Set(['Mouth', 'Eyes']));
  const [dragOverSlot, setDragOverSlot] = useState<string | null>(null);

  const togglePart = useCallback((partName: string) => {
    setExpandedParts(prev => {
      const newSet = new Set(prev);
      if (newSet.has(partName)) {
        newSet.delete(partName);
      } else {
        newSet.add(partName);
      }
      return newSet;
    });
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent, slotPath: string) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    setDragOverSlot(slotPath);
  }, []);

  const handleDragLeave = useCallback(() => {
    setDragOverSlot(null);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent, slotPath: string) => {
    e.preventDefault();
    setDragOverSlot(null);

    try {
      const data = JSON.parse(e.dataTransfer.getData('application/json'));
      if (data.type === 'slice') {
        // The actual slice object should be passed through a global registry
        // or we create a minimal slice object from the drag data
        const sliceFromDrag: ExtractedSlice = {
          id: data.sliceId,
          name: data.sliceName,
          psdPath: data.psdPath,
          image: new ImageData(1, 1), // Will be populated by parent
          canvas: document.createElement('canvas'), // Will be populated by parent
          bounds: data.bounds || { x: 0, y: 0, width: 0, height: 0 },
          mapped: false
        };
        onSlotDrop(slotPath, sliceFromDrag);
      }
    } catch (error) {
      console.error('Error parsing drop data:', error);
    }
  }, [onSlotDrop]);

  const renderSlot = useCallback((
    partName: string,
    slotName: string,
    slotConfig: any,
    slotPath: string
  ) => {
    const hasSlice = mappedSlices[slotPath];
    const isSelected = selectedSlot === slotPath;
    const isDragOver = dragOverSlot === slotPath;

    return (
      <div
        key={slotPath}
        className={`slot-item ${hasSlice ? 'has-slice' : 'empty'} ${isSelected ? 'selected' : ''} ${isDragOver ? 'drag-over' : ''}`}
        onClick={() => onSlotSelect(slotPath)}
        onDragOver={(e) => handleDragOver(e, slotPath)}
        onDragLeave={handleDragLeave}
        onDrop={(e) => handleDrop(e, slotPath)}
        title={`${slotPath}${hasSlice ? ` (${hasSlice.name})` : ' (empty)'}`}
      >
        <div className="slot-indicator">
          {hasSlice ? '●' : '○'}
        </div>
        <div className="slot-name">
          {slotName}
        </div>
        {hasSlice && (
          <div className="slice-preview">
            <canvas
              ref={(canvas) => {
                if (canvas && hasSlice.canvas) {
                  canvas.width = 24;
                  canvas.height = 24;
                  const ctx = canvas.getContext('2d');
                  if (ctx) {
                    ctx.drawImage(
                      hasSlice.canvas,
                      0, 0, hasSlice.canvas.width, hasSlice.canvas.height,
                      0, 0, 24, 24
                    );
                  }
                }
              }}
              width={24}
              height={24}
            />
          </div>
        )}
      </div>
    );
  }, [mappedSlices, selectedSlot, dragOverSlot, onSlotSelect, handleDragOver, handleDragLeave, handleDrop]);

  const renderSlotGroup = useCallback((
    partName: string,
    slotName: string,
    slotConfig: any,
    parentPath: string = ''
  ) => {
    const currentPath = parentPath ? `${parentPath}/${slotName}` : `${partName}/${slotName}`;

    if (Array.isArray(slotConfig)) {
      // Array of values (like visemes or emotions)
      return (
        <div key={currentPath} className="slot-group">
          <div className="slot-group-header">
            {slotName} ({slotConfig.length})
          </div>
          <div className="slot-group-items">
            {slotConfig.map(value => {
              const slotPath = `${currentPath}/${value}`;
              return renderSlot(partName, value, {}, slotPath);
            })}
          </div>
        </div>
      );
    } else if (typeof slotConfig === 'object' && slotConfig !== null && Object.keys(slotConfig).length > 0) {
      // Nested object (like Eye states)
      return (
        <div key={currentPath} className="slot-group">
          <div className="slot-group-header">
            {slotName}
          </div>
          <div className="slot-group-items">
            {Object.entries(slotConfig).map(([subKey, subConfig]) =>
              renderSlotGroup(partName, subKey, subConfig, currentPath)
            )}
          </div>
        </div>
      );
    } else {
      // Simple slot
      return renderSlot(partName, slotName, slotConfig, currentPath);
    }
  }, [renderSlot]);

  return (
    <div className="slot-palette">
      <div className="palette-header">
        <h3>Avatar Slots</h3>
        <div className="palette-stats">
          {Object.keys(mappedSlices).length} slots filled
        </div>
      </div>

      <div className="parts-list">
        {Object.entries(palette).map(([partName, partConfig]) => (
          <div key={partName} className="part-section">
            <div
              className={`part-header ${expandedParts.has(partName) ? 'expanded' : 'collapsed'}`}
              onClick={() => togglePart(partName)}
            >
              <span className="expand-icon">
                {expandedParts.has(partName) ? '▼' : '▶'}
              </span>
              <span className="part-name">{partName}</span>
              <span className="part-count">
                ({Object.keys(partConfig).length})
              </span>
            </div>

            {expandedParts.has(partName) && (
              <div className="part-content">
                {Object.entries(partConfig).map(([slotName, slotConfig]) =>
                  renderSlotGroup(partName, slotName, slotConfig)
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      <style jsx>{`
        .slot-palette {
          background: white;
          border: 1px solid #dee2e6;
          border-radius: 8px;
          padding: 16px;
          height: 100%;
          display: flex;
          flex-direction: column;
        }

        .palette-header {
          margin-bottom: 16px;
          border-bottom: 1px solid #e9ecef;
          padding-bottom: 12px;
        }

        .palette-header h3 {
          margin: 0 0 4px 0;
          color: #495057;
          font-size: 16px;
          font-weight: 600;
        }

        .palette-stats {
          font-size: 12px;
          color: #6c757d;
        }

        .parts-list {
          flex: 1;
          overflow-y: auto;
        }

        .part-section {
          margin-bottom: 12px;
        }

        .part-header {
          display: flex;
          align-items: center;
          padding: 8px 12px;
          background: #f8f9fa;
          border: 1px solid #e9ecef;
          border-radius: 6px;
          cursor: pointer;
          transition: background-color 0.2s ease;
        }

        .part-header:hover {
          background: #e9ecef;
        }

        .part-header.expanded {
          border-bottom-left-radius: 0;
          border-bottom-right-radius: 0;
          border-bottom: none;
        }

        .expand-icon {
          margin-right: 8px;
          font-size: 10px;
          color: #6c757d;
        }

        .part-name {
          flex: 1;
          font-weight: 600;
          color: #495057;
        }

        .part-count {
          font-size: 12px;
          color: #6c757d;
        }

        .part-content {
          border: 1px solid #e9ecef;
          border-top: none;
          border-bottom-left-radius: 6px;
          border-bottom-right-radius: 6px;
          padding: 12px;
          background: #fdfdfd;
        }

        .slot-group {
          margin-bottom: 12px;
        }

        .slot-group:last-child {
          margin-bottom: 0;
        }

        .slot-group-header {
          font-size: 12px;
          font-weight: 600;
          color: #6c757d;
          margin-bottom: 6px;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .slot-group-items {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
          gap: 6px;
        }

        .slot-item {
          display: flex;
          align-items: center;
          padding: 6px 8px;
          border: 1px solid #e9ecef;
          border-radius: 4px;
          cursor: pointer;
          transition: all 0.2s ease;
          background: white;
          min-height: 32px;
        }

        .slot-item:hover {
          border-color: #007bff;
          background: #f8f9ff;
        }

        .slot-item.selected {
          border-color: #007bff;
          background: #e7f3ff;
          box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
        }

        .slot-item.has-slice {
          border-color: #28a745;
          background: #f8fff9;
        }

        .slot-item.has-slice:hover {
          border-color: #20c997;
        }

        .slot-item.drag-over {
          border-color: #ffc107;
          background: #fffbf0;
          box-shadow: 0 0 0 2px rgba(255, 193, 7, 0.25);
        }

        .slot-indicator {
          margin-right: 6px;
          font-size: 12px;
          font-weight: bold;
        }

        .slot-item.empty .slot-indicator {
          color: #dee2e6;
        }

        .slot-item.has-slice .slot-indicator {
          color: #28a745;
        }

        .slot-name {
          flex: 1;
          font-size: 11px;
          color: #495057;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .slice-preview {
          margin-left: 4px;
        }

        .slice-preview canvas {
          border: 1px solid #e9ecef;
          border-radius: 2px;
        }
      `}</style>
    </div>
  );
};

export default SlotPalette;