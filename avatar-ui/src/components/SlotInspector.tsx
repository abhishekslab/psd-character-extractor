import React, { useState } from 'react';
import { ExtractedSlice } from '../types/avatar';

interface SlotInspectorProps {
  selectedSlot: string | null;
  slice: ExtractedSlice | null;
  onRemoveSlice: (slotPath: string) => void;
  onReplaceSlice: (slotPath: string) => void;
  onNudgeZ: (slotPath: string, offset: number) => void;
  onTint: (slotPath: string, tint: string) => void;
  zOffset: number;
  tint: string;
}

const SlotInspector: React.FC<SlotInspectorProps> = ({
  selectedSlot,
  slice,
  onRemoveSlice,
  onReplaceSlice,
  onNudgeZ,
  onTint,
  zOffset,
  tint
}) => {
  const [localTint, setLocalTint] = useState(tint);

  const handleTintChange = (newTint: string) => {
    setLocalTint(newTint);
    if (selectedSlot) {
      onTint(selectedSlot, newTint);
    }
  };

  const handleZOffsetChange = (delta: number) => {
    if (selectedSlot) {
      const newOffset = Math.max(-2, Math.min(2, zOffset + delta));
      onNudgeZ(selectedSlot, newOffset);
    }
  };

  if (!selectedSlot) {
    return (
      <div className="slot-inspector">
        <div className="inspector-header">
          <h3>Slot Inspector</h3>
        </div>
        <div className="empty-state">
          Select a slot to view details
        </div>

        <style jsx>{`
          .slot-inspector {
            background: white;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 16px;
            height: 100%;
            display: flex;
            flex-direction: column;
          }

          .inspector-header h3 {
            margin: 0 0 16px 0;
            color: #495057;
            font-size: 16px;
            font-weight: 600;
          }

          .empty-state {
            text-align: center;
            color: #6c757d;
            font-style: italic;
            padding: 40px 20px;
          }
        `}</style>
      </div>
    );
  }

  return (
    <div className="slot-inspector">
      <div className="inspector-header">
        <h3>Slot Inspector</h3>
        <div className="slot-path">{selectedSlot}</div>
      </div>

      {slice ? (
        <div className="slice-details">
          <div className="slice-preview-section">
            <h4>Preview</h4>
            <div className="slice-preview">
              <canvas
                ref={(canvas) => {
                  if (canvas && slice.canvas) {
                    canvas.width = 128;
                    canvas.height = 128;
                    const ctx = canvas.getContext('2d');
                    if (ctx) {
                      // Clear canvas
                      ctx.clearRect(0, 0, 128, 128);

                      // Calculate scale to fit
                      const scale = Math.min(
                        128 / slice.canvas.width,
                        128 / slice.canvas.height
                      );

                      const scaledWidth = slice.canvas.width * scale;
                      const scaledHeight = slice.canvas.height * scale;
                      const x = (128 - scaledWidth) / 2;
                      const y = (128 - scaledHeight) / 2;

                      ctx.drawImage(
                        slice.canvas,
                        x, y, scaledWidth, scaledHeight
                      );

                      // Apply tint if specified
                      if (localTint && localTint !== '#ffffff') {
                        ctx.globalCompositeOperation = 'multiply';
                        ctx.fillStyle = localTint;
                        ctx.fillRect(x, y, scaledWidth, scaledHeight);
                        ctx.globalCompositeOperation = 'source-over';
                      }
                    }
                  }
                }}
                width={128}
                height={128}
              />
            </div>
          </div>

          <div className="slice-info-section">
            <h4>Slice Information</h4>
            <div className="info-grid">
              <div className="info-item">
                <label>Name:</label>
                <span>{slice.name}</span>
              </div>
              <div className="info-item">
                <label>PSD Path:</label>
                <span title={slice.psdPath}>{slice.psdPath}</span>
              </div>
              <div className="info-item">
                <label>Dimensions:</label>
                <span>{slice.bounds.width} × {slice.bounds.height}</span>
              </div>
              <div className="info-item">
                <label>Position:</label>
                <span>({slice.bounds.x}, {slice.bounds.y})</span>
              </div>
            </div>
          </div>

          <div className="controls-section">
            <h4>Controls</h4>

            <div className="control-group">
              <label>Z-Order Offset:</label>
              <div className="z-control">
                <button
                  onClick={() => handleZOffsetChange(-1)}
                  disabled={zOffset <= -2}
                  className="z-button"
                >
                  -
                </button>
                <span className="z-value">{zOffset}</span>
                <button
                  onClick={() => handleZOffsetChange(1)}
                  disabled={zOffset >= 2}
                  className="z-button"
                >
                  +
                </button>
              </div>
              <div className="help-text">
                Adjust draw order (-2 to +2)
              </div>
            </div>

            <div className="control-group">
              <label>Tint Color:</label>
              <div className="tint-control">
                <input
                  type="color"
                  value={localTint}
                  onChange={(e) => handleTintChange(e.target.value)}
                  className="color-picker"
                />
                <input
                  type="text"
                  value={localTint}
                  onChange={(e) => handleTintChange(e.target.value)}
                  className="color-input"
                  placeholder="#ffffff"
                />
                <button
                  onClick={() => handleTintChange('#ffffff')}
                  className="reset-button"
                >
                  Reset
                </button>
              </div>
            </div>
          </div>

          <div className="actions-section">
            <h4>Actions</h4>
            <div className="action-buttons">
              <button
                onClick={() => onReplaceSlice(selectedSlot)}
                className="action-button replace"
              >
                Replace Slice
              </button>
              <button
                onClick={() => onRemoveSlice(selectedSlot)}
                className="action-button remove"
              >
                Remove Slice
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div className="empty-slot">
          <div className="empty-slot-icon">○</div>
          <div className="empty-slot-text">Empty Slot</div>
          <div className="empty-slot-help">
            Drag a slice from the unmapped panel to fill this slot
          </div>
          <button
            onClick={() => onReplaceSlice(selectedSlot)}
            className="action-button assign"
          >
            Assign Slice
          </button>
        </div>
      )}

      <style jsx>{`
        .slot-inspector {
          background: white;
          border: 1px solid #dee2e6;
          border-radius: 8px;
          padding: 16px;
          height: 100%;
          display: flex;
          flex-direction: column;
          overflow-y: auto;
        }

        .inspector-header {
          margin-bottom: 16px;
          border-bottom: 1px solid #e9ecef;
          padding-bottom: 12px;
        }

        .inspector-header h3 {
          margin: 0 0 4px 0;
          color: #495057;
          font-size: 16px;
          font-weight: 600;
        }

        .slot-path {
          font-size: 12px;
          color: #6c757d;
          font-family: monospace;
          word-break: break-all;
        }

        .slice-details {
          flex: 1;
        }

        .slice-preview-section,
        .slice-info-section,
        .controls-section,
        .actions-section {
          margin-bottom: 20px;
        }

        .slice-preview-section h4,
        .slice-info-section h4,
        .controls-section h4,
        .actions-section h4 {
          margin: 0 0 8px 0;
          color: #495057;
          font-size: 14px;
          font-weight: 600;
        }

        .slice-preview {
          display: flex;
          justify-content: center;
          padding: 12px;
          background: #f8f9fa;
          border: 1px solid #e9ecef;
          border-radius: 6px;
        }

        .slice-preview canvas {
          border: 1px solid #dee2e6;
          background: white;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }

        .info-grid {
          display: grid;
          gap: 8px;
        }

        .info-item {
          display: grid;
          grid-template-columns: 80px 1fr;
          gap: 8px;
          align-items: center;
        }

        .info-item label {
          font-size: 12px;
          font-weight: 600;
          color: #6c757d;
        }

        .info-item span {
          font-size: 12px;
          color: #495057;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .control-group {
          margin-bottom: 16px;
        }

        .control-group label {
          display: block;
          font-size: 12px;
          font-weight: 600;
          color: #495057;
          margin-bottom: 6px;
        }

        .z-control {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .z-button {
          width: 32px;
          height: 32px;
          border: 1px solid #ced4da;
          background: white;
          border-radius: 4px;
          cursor: pointer;
          font-weight: bold;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .z-button:hover:not(:disabled) {
          background: #f8f9fa;
          border-color: #adb5bd;
        }

        .z-button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .z-value {
          font-weight: 600;
          min-width: 20px;
          text-align: center;
        }

        .help-text {
          font-size: 10px;
          color: #6c757d;
          margin-top: 4px;
        }

        .tint-control {
          display: flex;
          gap: 8px;
          align-items: center;
        }

        .color-picker {
          width: 40px;
          height: 32px;
          border: 1px solid #ced4da;
          border-radius: 4px;
          cursor: pointer;
        }

        .color-input {
          flex: 1;
          padding: 6px 8px;
          border: 1px solid #ced4da;
          border-radius: 4px;
          font-size: 12px;
          font-family: monospace;
        }

        .reset-button {
          padding: 6px 12px;
          border: 1px solid #ced4da;
          background: white;
          border-radius: 4px;
          cursor: pointer;
          font-size: 12px;
        }

        .reset-button:hover {
          background: #f8f9fa;
        }

        .action-buttons {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .action-button {
          padding: 8px 16px;
          border: 1px solid #ced4da;
          border-radius: 4px;
          cursor: pointer;
          font-size: 14px;
          font-weight: 500;
          transition: all 0.2s ease;
        }

        .action-button.replace {
          background: #007bff;
          color: white;
          border-color: #007bff;
        }

        .action-button.replace:hover {
          background: #0056b3;
          border-color: #0056b3;
        }

        .action-button.remove {
          background: #dc3545;
          color: white;
          border-color: #dc3545;
        }

        .action-button.remove:hover {
          background: #c82333;
          border-color: #c82333;
        }

        .action-button.assign {
          background: #28a745;
          color: white;
          border-color: #28a745;
        }

        .action-button.assign:hover {
          background: #218838;
          border-color: #218838;
        }

        .empty-slot {
          text-align: center;
          padding: 40px 20px;
          color: #6c757d;
        }

        .empty-slot-icon {
          font-size: 48px;
          margin-bottom: 16px;
          color: #dee2e6;
        }

        .empty-slot-text {
          font-size: 16px;
          font-weight: 600;
          margin-bottom: 8px;
        }

        .empty-slot-help {
          font-size: 12px;
          margin-bottom: 20px;
          line-height: 1.4;
        }
      `}</style>
    </div>
  );
};

export default SlotInspector;