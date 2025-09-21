import React, { useState, useCallback } from 'react';
import { ExtractedSlice } from '../types/avatar';

interface UnmappedSlicesPanelProps {
  slices: ExtractedSlice[];
  onSliceSelect: (slice: ExtractedSlice) => void;
  selectedSlices: ExtractedSlice[];
  onSearch: (query: string) => void;
  searchQuery: string;
}

const UnmappedSlicesPanel: React.FC<UnmappedSlicesPanelProps> = ({
  slices,
  onSliceSelect,
  selectedSlices,
  onSearch,
  searchQuery
}) => {
  const [draggedSlice, setDraggedSlice] = useState<ExtractedSlice | null>(null);

  const handleDragStart = useCallback((e: React.DragEvent, slice: ExtractedSlice) => {
    setDraggedSlice(slice);
    e.dataTransfer.setData('application/json', JSON.stringify({
      type: 'slice',
      sliceId: slice.id,
      sliceName: slice.name,
      psdPath: slice.psdPath
    }));
    e.dataTransfer.effectAllowed = 'move';
  }, []);

  const handleDragEnd = useCallback(() => {
    setDraggedSlice(null);
  }, []);

  const isSelected = useCallback((slice: ExtractedSlice) => {
    return selectedSlices.some(s => s.id === slice.id);
  }, [selectedSlices]);

  const createThumbnail = (slice: ExtractedSlice): string => {
    // Create a smaller thumbnail version
    const thumbnailCanvas = document.createElement('canvas');
    const thumbnailCtx = thumbnailCanvas.getContext('2d');

    if (!thumbnailCtx) return '';

    const maxSize = 64;
    const aspectRatio = slice.bounds.width / slice.bounds.height;

    if (aspectRatio > 1) {
      thumbnailCanvas.width = maxSize;
      thumbnailCanvas.height = maxSize / aspectRatio;
    } else {
      thumbnailCanvas.width = maxSize * aspectRatio;
      thumbnailCanvas.height = maxSize;
    }

    thumbnailCtx.drawImage(
      slice.canvas,
      0, 0, slice.canvas.width, slice.canvas.height,
      0, 0, thumbnailCanvas.width, thumbnailCanvas.height
    );

    return thumbnailCanvas.toDataURL();
  };

  const filteredSlices = slices.filter(slice => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      slice.name.toLowerCase().includes(query) ||
      slice.psdPath.toLowerCase().includes(query)
    );
  });

  return (
    <div className="unmapped-slices-panel">
      <div className="panel-header">
        <h3>Unmapped Slices ({filteredSlices.length})</h3>
        <div className="search-container">
          <input
            type="text"
            placeholder="Search slices..."
            value={searchQuery}
            onChange={(e) => onSearch(e.target.value)}
            className="search-input"
          />
        </div>
      </div>

      <div className="slices-grid">
        {filteredSlices.map((slice) => (
          <div
            key={slice.id}
            className={`slice-item ${isSelected(slice) ? 'selected' : ''} ${
              draggedSlice?.id === slice.id ? 'dragging' : ''
            }`}
            draggable
            onDragStart={(e) => handleDragStart(e, slice)}
            onDragEnd={handleDragEnd}
            onClick={() => onSliceSelect(slice)}
            title={`${slice.name}\nPath: ${slice.psdPath}\nSize: ${slice.bounds.width}×${slice.bounds.height}`}
          >
            <div className="slice-thumbnail">
              <img
                src={createThumbnail(slice)}
                alt={slice.name}
                draggable={false}
              />
            </div>
            <div className="slice-info">
              <div className="slice-name" title={slice.name}>
                {slice.name}
              </div>
              <div className="slice-path" title={slice.psdPath}>
                {slice.psdPath}
              </div>
              <div className="slice-dimensions">
                {slice.bounds.width}×{slice.bounds.height}
              </div>
            </div>
          </div>
        ))}
      </div>

      {filteredSlices.length === 0 && (
        <div className="empty-state">
          {searchQuery ? 'No slices match your search' : 'All slices have been mapped!'}
        </div>
      )}

      <style jsx>{`
        .unmapped-slices-panel {
          background: #f8f9fa;
          border: 1px solid #dee2e6;
          border-radius: 8px;
          padding: 16px;
          height: 100%;
          display: flex;
          flex-direction: column;
        }

        .panel-header {
          margin-bottom: 16px;
        }

        .panel-header h3 {
          margin: 0 0 8px 0;
          color: #495057;
          font-size: 16px;
          font-weight: 600;
        }

        .search-container {
          margin-bottom: 8px;
        }

        .search-input {
          width: 100%;
          padding: 8px 12px;
          border: 1px solid #ced4da;
          border-radius: 4px;
          font-size: 14px;
        }

        .search-input:focus {
          outline: none;
          border-color: #80bdff;
          box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
        }

        .slices-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
          gap: 12px;
          flex: 1;
          overflow-y: auto;
          max-height: calc(100vh - 200px);
        }

        .slice-item {
          background: white;
          border: 2px solid #e9ecef;
          border-radius: 8px;
          padding: 12px;
          cursor: move;
          transition: all 0.2s ease;
          display: flex;
          flex-direction: column;
          align-items: center;
          text-align: center;
        }

        .slice-item:hover {
          border-color: #007bff;
          box-shadow: 0 2px 8px rgba(0, 123, 255, 0.15);
          transform: translateY(-1px);
        }

        .slice-item.selected {
          border-color: #007bff;
          background: #f8f9ff;
        }

        .slice-item.dragging {
          opacity: 0.5;
          transform: rotate(5deg);
        }

        .slice-thumbnail {
          width: 64px;
          height: 64px;
          display: flex;
          align-items: center;
          justify-content: center;
          margin-bottom: 8px;
          border: 1px solid #e9ecef;
          border-radius: 4px;
          overflow: hidden;
          background: white;
        }

        .slice-thumbnail img {
          max-width: 100%;
          max-height: 100%;
          object-fit: contain;
        }

        .slice-info {
          width: 100%;
        }

        .slice-name {
          font-weight: 600;
          font-size: 12px;
          color: #495057;
          margin-bottom: 4px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .slice-path {
          font-size: 10px;
          color: #6c757d;
          margin-bottom: 4px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .slice-dimensions {
          font-size: 10px;
          color: #868e96;
          font-weight: 500;
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
};

export default UnmappedSlicesPanel;