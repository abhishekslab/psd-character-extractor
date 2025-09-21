import React, { useState, useCallback } from 'react';
import { ExtractedSlice, Item } from '../types/avatar';

interface WardrobePanelProps {
  mappedSlices: Record<string, ExtractedSlice>;
  selectedSlices: ExtractedSlice[];
  onCreateItem: (item: Omit<Item, 'slices'> & { selectedSlots: string[] }) => void;
  existingItems: Item[];
  onEquipItem: (item: Item) => void;
  onUnequipItem: (item: Item) => void;
  equippedItems: Item[];
}

interface ItemFormData {
  type: string;
  sku: string;
  rigId: string;
  tags: string;
  license: string;
}

const WardrobePanel: React.FC<WardrobePanelProps> = ({
  mappedSlices,
  selectedSlices,
  onCreateItem,
  existingItems,
  onEquipItem,
  onUnequipItem,
  equippedItems
}) => {
  const [activeTab, setActiveTab] = useState<'create' | 'browse'>('create');
  const [formData, setFormData] = useState<ItemFormData>({
    type: 'hair',
    sku: '',
    rigId: 'anime-1024-headA-v1',
    tags: '',
    license: 'CC-BY-4.0'
  });
  const [selectedSlots, setSelectedSlots] = useState<string[]>([]);

  const itemTypes = [
    'hair', 'top', 'bottom', 'outerwear', 'shoes',
    'glasses', 'earrings', 'hat', 'mask', 'fx'
  ];

  const handleFormChange = useCallback((field: keyof ItemFormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  }, []);

  const handleSlotToggle = useCallback((slotPath: string) => {
    setSelectedSlots(prev => {
      if (prev.includes(slotPath)) {
        return prev.filter(slot => slot !== slotPath);
      } else {
        return [...prev, slotPath];
      }
    });
  }, []);

  const handleCreateItem = useCallback(() => {
    if (!formData.sku || selectedSlots.length === 0) {
      alert('Please provide an SKU and select at least one slot');
      return;
    }

    // Calculate fit box based on selected slices
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;

    selectedSlots.forEach(slotPath => {
      const slice = mappedSlices[slotPath];
      if (slice) {
        minX = Math.min(minX, slice.bounds.x);
        minY = Math.min(minY, slice.bounds.y);
        maxX = Math.max(maxX, slice.bounds.x + slice.bounds.width);
        maxY = Math.max(maxY, slice.bounds.y + slice.bounds.height);
      }
    });

    const fitBox = {
      x: minX,
      y: minY,
      w: maxX - minX,
      h: maxY - minY
    };

    const newItem: Omit<Item, 'slices'> & { selectedSlots: string[] } = {
      type: formData.type,
      sku: formData.sku,
      rigId: formData.rigId,
      fills: selectedSlots,
      zOffsets: Object.fromEntries(selectedSlots.map(slot => [slot, 0])),
      fitBox,
      selectedSlots,
      variants: [
        { name: 'default', tint: '#ffffff' }
      ],
      tags: formData.tags ? formData.tags.split(',').map(tag => tag.trim()) : [],
      license: formData.license || undefined
    };

    onCreateItem(newItem);

    // Reset form
    setFormData(prev => ({ ...prev, sku: '', tags: '' }));
    setSelectedSlots([]);
  }, [formData, selectedSlots, mappedSlices, onCreateItem]);

  const isEquipped = useCallback((item: Item) => {
    return equippedItems.some(equipped =>
      equipped.type === item.type && equipped.sku === item.sku
    );
  }, [equippedItems]);

  const renderCreateTab = () => (
    <div className="wardrobe-create">
      <h4>Create Wardrobe Item</h4>

      <div className="form-section">
        <div className="form-group">
          <label>Item Type:</label>
          <select
            value={formData.type}
            onChange={(e) => handleFormChange('type', e.target.value)}
          >
            {itemTypes.map(type => (
              <option key={type} value={type}>
                {type.charAt(0).toUpperCase() + type.slice(1)}
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label>SKU (Item ID):</label>
          <input
            type="text"
            value={formData.sku}
            onChange={(e) => handleFormChange('sku', e.target.value)}
            placeholder="e.g., short_bob, hoodie_blue"
          />
        </div>

        <div className="form-group">
          <label>Rig ID:</label>
          <input
            type="text"
            value={formData.rigId}
            onChange={(e) => handleFormChange('rigId', e.target.value)}
            placeholder="anime-1024-headA-v1"
          />
        </div>

        <div className="form-group">
          <label>Tags (comma-separated):</label>
          <input
            type="text"
            value={formData.tags}
            onChange={(e) => handleFormChange('tags', e.target.value)}
            placeholder="cute, short, bob"
          />
        </div>

        <div className="form-group">
          <label>License:</label>
          <input
            type="text"
            value={formData.license}
            onChange={(e) => handleFormChange('license', e.target.value)}
            placeholder="CC-BY-4.0"
          />
        </div>
      </div>

      <div className="slot-selection">
        <h5>Select Slots to Include:</h5>
        <div className="slot-list">
          {Object.entries(mappedSlices).map(([slotPath, slice]) => (
            <div
              key={slotPath}
              className={`slot-item ${selectedSlots.includes(slotPath) ? 'selected' : ''}`}
              onClick={() => handleSlotToggle(slotPath)}
            >
              <div className="slot-preview">
                <canvas
                  ref={(canvas) => {
                    if (canvas && slice.canvas) {
                      canvas.width = 32;
                      canvas.height = 32;
                      const ctx = canvas.getContext('2d');
                      if (ctx) {
                        ctx.drawImage(
                          slice.canvas,
                          0, 0, slice.canvas.width, slice.canvas.height,
                          0, 0, 32, 32
                        );
                      }
                    }
                  }}
                  width={32}
                  height={32}
                />
              </div>
              <div className="slot-info">
                <div className="slot-name">{slotPath}</div>
                <div className="slice-name">{slice.name}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <button
        className="create-button"
        onClick={handleCreateItem}
        disabled={!formData.sku || selectedSlots.length === 0}
      >
        Create Item
      </button>
    </div>
  );

  const renderBrowseTab = () => (
    <div className="wardrobe-browse">
      <h4>Wardrobe Items ({existingItems.length})</h4>

      {existingItems.length === 0 ? (
        <div className="empty-wardrobe">
          <p>No wardrobe items created yet.</p>
          <p>Switch to the Create tab to make items from your mapped slices.</p>
        </div>
      ) : (
        <div className="items-grid">
          {existingItems.map((item, index) => (
            <div key={`${item.type}-${item.sku}`} className="wardrobe-item">
              <div className="item-preview">
                {/* Simple preview - in a real implementation, this would render the item */}
                <div className="item-type-badge">{item.type}</div>
              </div>

              <div className="item-info">
                <div className="item-name">{item.sku}</div>
                <div className="item-details">
                  <span>{item.fills.length} slots</span>
                  {item.tags && item.tags.length > 0 && (
                    <span className="tags">
                      {item.tags.slice(0, 2).join(', ')}
                      {item.tags.length > 2 && '...'}
                    </span>
                  )}
                </div>
              </div>

              <div className="item-actions">
                {isEquipped(item) ? (
                  <button
                    className="action-button unequip"
                    onClick={() => onUnequipItem(item)}
                  >
                    Unequip
                  </button>
                ) : (
                  <button
                    className="action-button equip"
                    onClick={() => onEquipItem(item)}
                  >
                    Equip
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  return (
    <div className="wardrobe-panel">
      <div className="panel-header">
        <h3>Wardrobe System</h3>
        <div className="tab-buttons">
          <button
            className={`tab-button ${activeTab === 'create' ? 'active' : ''}`}
            onClick={() => setActiveTab('create')}
          >
            Create
          </button>
          <button
            className={`tab-button ${activeTab === 'browse' ? 'active' : ''}`}
            onClick={() => setActiveTab('browse')}
          >
            Browse ({existingItems.length})
          </button>
        </div>
      </div>

      <div className="panel-content">
        {activeTab === 'create' ? renderCreateTab() : renderBrowseTab()}
      </div>

      <style jsx>{`
        .wardrobe-panel {
          background: white;
          border: 1px solid #dee2e6;
          border-radius: 8px;
          padding: 16px;
          height: 100%;
          display: flex;
          flex-direction: column;
        }

        .panel-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
          border-bottom: 1px solid #e9ecef;
          padding-bottom: 12px;
        }

        .panel-header h3 {
          margin: 0;
          color: #495057;
          font-size: 16px;
          font-weight: 600;
        }

        .tab-buttons {
          display: flex;
          gap: 4px;
        }

        .tab-button {
          padding: 6px 12px;
          border: 1px solid #ced4da;
          background: #f8f9fa;
          border-radius: 4px;
          cursor: pointer;
          font-size: 12px;
          transition: all 0.2s ease;
        }

        .tab-button:hover {
          background: #e9ecef;
        }

        .tab-button.active {
          background: #007bff;
          color: white;
          border-color: #007bff;
        }

        .panel-content {
          flex: 1;
          overflow-y: auto;
        }

        .wardrobe-create h4,
        .wardrobe-browse h4 {
          margin: 0 0 16px 0;
          color: #495057;
          font-size: 14px;
          font-weight: 600;
        }

        .form-section {
          margin-bottom: 20px;
        }

        .form-group {
          margin-bottom: 12px;
        }

        .form-group label {
          display: block;
          font-size: 12px;
          font-weight: 600;
          color: #495057;
          margin-bottom: 4px;
        }

        .form-group input,
        .form-group select {
          width: 100%;
          padding: 6px 8px;
          border: 1px solid #ced4da;
          border-radius: 4px;
          font-size: 12px;
        }

        .slot-selection h5 {
          margin: 0 0 8px 0;
          color: #495057;
          font-size: 12px;
          font-weight: 600;
        }

        .slot-list {
          max-height: 200px;
          overflow-y: auto;
          border: 1px solid #e9ecef;
          border-radius: 4px;
          padding: 8px;
        }

        .slot-item {
          display: flex;
          align-items: center;
          padding: 6px;
          border: 1px solid transparent;
          border-radius: 4px;
          cursor: pointer;
          margin-bottom: 4px;
          transition: all 0.2s ease;
        }

        .slot-item:hover {
          background: #f8f9fa;
          border-color: #ced4da;
        }

        .slot-item.selected {
          background: #e7f3ff;
          border-color: #007bff;
        }

        .slot-preview {
          margin-right: 8px;
          border: 1px solid #e9ecef;
          border-radius: 2px;
        }

        .slot-preview canvas {
          display: block;
        }

        .slot-info {
          flex: 1;
          min-width: 0;
        }

        .slot-name {
          font-size: 10px;
          font-weight: 600;
          color: #495057;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .slice-name {
          font-size: 9px;
          color: #6c757d;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .create-button {
          width: 100%;
          padding: 10px 16px;
          background: #28a745;
          color: white;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          font-size: 14px;
          font-weight: 500;
          transition: all 0.2s ease;
        }

        .create-button:hover:not(:disabled) {
          background: #218838;
        }

        .create-button:disabled {
          background: #6c757d;
          cursor: not-allowed;
        }

        .empty-wardrobe {
          text-align: center;
          color: #6c757d;
          padding: 40px 20px;
          font-size: 12px;
          line-height: 1.4;
        }

        .items-grid {
          display: grid;
          grid-template-columns: 1fr;
          gap: 12px;
        }

        .wardrobe-item {
          border: 1px solid #e9ecef;
          border-radius: 6px;
          padding: 12px;
          transition: all 0.2s ease;
        }

        .wardrobe-item:hover {
          border-color: #ced4da;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }

        .item-preview {
          position: relative;
          height: 60px;
          background: #f8f9fa;
          border-radius: 4px;
          margin-bottom: 8px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .item-type-badge {
          background: #007bff;
          color: white;
          padding: 4px 8px;
          border-radius: 4px;
          font-size: 10px;
          font-weight: 600;
          text-transform: uppercase;
        }

        .item-info {
          margin-bottom: 8px;
        }

        .item-name {
          font-size: 12px;
          font-weight: 600;
          color: #495057;
          margin-bottom: 2px;
        }

        .item-details {
          font-size: 10px;
          color: #6c757d;
          display: flex;
          gap: 8px;
        }

        .tags {
          font-style: italic;
        }

        .item-actions {
          display: flex;
          gap: 6px;
        }

        .action-button {
          flex: 1;
          padding: 6px 12px;
          border: 1px solid #ced4da;
          border-radius: 4px;
          cursor: pointer;
          font-size: 11px;
          font-weight: 500;
          transition: all 0.2s ease;
        }

        .action-button.equip {
          background: #28a745;
          color: white;
          border-color: #28a745;
        }

        .action-button.equip:hover {
          background: #218838;
          border-color: #218838;
        }

        .action-button.unequip {
          background: #dc3545;
          color: white;
          border-color: #dc3545;
        }

        .action-button.unequip:hover {
          background: #c82333;
          border-color: #c82333;
        }
      `}</style>
    </div>
  );
};

export default WardrobePanel;