import PSD from 'psd.js';
import type { ExtractedSlice } from '../types/avatar';

export class PSDProcessor {
  private psd: any = null;

  async loadPSD(file: File): Promise<void> {
    try {
      const arrayBuffer = await file.arrayBuffer();
      const uint8Array = new Uint8Array(arrayBuffer);

      // Create PSD instance and parse
      this.psd = new PSD(uint8Array);
      this.psd.parse();

      console.log('PSD loaded successfully:', {
        width: this.psd.header?.width,
        height: this.psd.header?.height,
        hasTree: !!this.psd.tree
      });

    } catch (error) {
      console.error('Error loading PSD:', error);
      throw new Error(`Failed to load PSD: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  getPSDDimensions(): { width: number; height: number } {
    if (!this.psd || !this.psd.header) {
      return { width: 1024, height: 1024 };
    }

    return {
      width: this.psd.header.width || 1024,
      height: this.psd.header.height || 1024
    };
  }

  getLayerTree(): any[] {
    if (!this.psd) {
      return [];
    }

    try {
      // Different ways the API might expose layers
      if (this.psd.tree && typeof this.psd.tree === 'function') {
        const tree = this.psd.tree();
        return tree.children ? (typeof tree.children === 'function' ? tree.children() : tree.children) : [];
      }

      if (this.psd.tree && this.psd.tree.children) {
        return Array.isArray(this.psd.tree.children) ? this.psd.tree.children : [];
      }

      // Try to access layers directly
      if (this.psd.layers) {
        return Array.isArray(this.psd.layers) ? this.psd.layers : [];
      }

      return [];
    } catch (error) {
      console.error('Error getting layer tree:', error);
      return [];
    }
  }

  async extractAllSlices(): Promise<ExtractedSlice[]> {
    if (!this.psd) {
      throw new Error('No PSD loaded');
    }

    console.log('Starting slice extraction...');

    const slices: ExtractedSlice[] = [];

    try {
      // Try different approaches to get layers
      let layers: any[] = [];

      // Method 1: Try tree() function
      try {
        if (this.psd.tree && typeof this.psd.tree === 'function') {
          const tree = this.psd.tree();
          if (tree && tree.children) {
            layers = typeof tree.children === 'function' ? tree.children() : tree.children;
          }
        }
      } catch (e) {
        console.log('Method 1 failed, trying method 2');
      }

      // Method 2: Try direct tree access
      if (layers.length === 0) {
        try {
          if (this.psd.tree && this.psd.tree.children) {
            layers = Array.isArray(this.psd.tree.children) ? this.psd.tree.children : [];
          }
        } catch (e) {
          console.log('Method 2 failed, trying method 3');
        }
      }

      // Method 3: Try layers property
      if (layers.length === 0) {
        try {
          if (this.psd.layers) {
            layers = Array.isArray(this.psd.layers) ? this.psd.layers : [];
          }
        } catch (e) {
          console.log('Method 3 failed');
        }
      }

      console.log(`Found ${layers.length} top-level layers`);

      if (layers.length === 0) {
        throw new Error('No layers found in PSD file');
      }

      // Flatten all layers
      const flatLayers = this.flattenLayers(layers);
      console.log(`Flattened to ${flatLayers.length} individual layers`);

      // Process each layer
      for (let i = 0; i < flatLayers.length; i++) {
        const layer = flatLayers[i];
        console.log(`Processing layer ${i + 1}/${flatLayers.length}: ${layer.name || 'Unnamed'}`);

        try {
          const slice = await this.createSliceFromLayer(layer, i);
          if (slice) {
            slices.push(slice);
          }
        } catch (error) {
          console.error(`Failed to process layer ${layer.name || 'Unnamed'}:`, error);
          // Continue with other layers
        }
      }

      console.log(`Successfully extracted ${slices.length} slices`);
      return slices;

    } catch (error) {
      console.error('Error during slice extraction:', error);
      throw new Error(`Failed to extract slices: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  private flattenLayers(layers: any[], parentPath: string = ''): any[] {
    const flattened: any[] = [];

    for (let i = 0; i < layers.length; i++) {
      const layer = layers[i];

      try {
        // Get layer name safely
        let name = 'Unnamed';
        try {
          if (typeof layer.name === 'function') {
            name = layer.name();
          } else if (typeof layer.name === 'string') {
            name = layer.name;
          }
        } catch (e) {
          console.log('Could not get layer name');
        }

        const path = parentPath ? `${parentPath}/${name}` : name;

        // Check if layer has children
        let children: any[] = [];
        try {
          if (layer.children) {
            if (typeof layer.children === 'function') {
              children = layer.children();
            } else if (Array.isArray(layer.children)) {
              children = layer.children;
            }
          }
        } catch (e) {
          // No children or error accessing them
        }

        if (children && children.length > 0) {
          // Recursively flatten children
          flattened.push(...this.flattenLayers(children, path));
        } else {
          // Add this layer with computed path
          flattened.push({
            ...layer,
            computedName: name,
            computedPath: path
          });
        }
      } catch (error) {
        console.error(`Error processing layer ${i}:`, error);
        // Continue with other layers
      }
    }

    return flattened;
  }

  private async createSliceFromLayer(layer: any, index: number): Promise<ExtractedSlice | null> {
    try {
      // Get layer properties safely
      const name = layer.computedName || 'Unnamed';
      const path = layer.computedPath || name;

      // Get dimensions
      let bounds = { x: 0, y: 0, width: 100, height: 100 };

      try {
        // Try different ways to get bounds
        if (typeof layer.left === 'function') {
          bounds.x = layer.left() || 0;
          bounds.y = layer.top() || 0;
          bounds.width = (layer.right() || 100) - bounds.x;
          bounds.height = (layer.bottom() || 100) - bounds.y;
        } else {
          bounds.x = layer.left || 0;
          bounds.y = layer.top || 0;
          bounds.width = (layer.right || 100) - bounds.x;
          bounds.height = (layer.bottom || 100) - bounds.y;
        }
      } catch (e) {
        console.log('Using default bounds for layer:', name);
      }

      // Ensure positive dimensions
      if (bounds.width <= 0) bounds.width = 100;
      if (bounds.height <= 0) bounds.height = 100;

      // Create a simple canvas for this layer
      const canvas = this.createLayerCanvas(name, bounds.width, bounds.height);
      const ctx = canvas.getContext('2d')!;
      const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);

      const slice: ExtractedSlice = {
        id: `slice_${index.toString().padStart(3, '0')}`,
        name,
        psdPath: path,
        image: imageData,
        canvas,
        bounds,
        mapped: false
      };

      return slice;

    } catch (error) {
      console.error('Error creating slice from layer:', error);
      return null;
    }
  }

  private createLayerCanvas(name: string, width: number, height: number): HTMLCanvasElement {
    const canvas = document.createElement('canvas');
    canvas.width = Math.max(width, 1);
    canvas.height = Math.max(height, 1);

    const ctx = canvas.getContext('2d')!;

    // Create a colored rectangle based on layer name
    const colors: Record<string, string> = {
      'hair': '#8B4513',
      'eye': '#4169E1',
      'mouth': '#FF6B6B',
      'body': '#FFB6C1',
      'face': '#FDBCB4',
      'cloth': '#87CEEB',
      'accessory': '#DDA0DD',
      'background': '#F0F0F0'
    };

    // Find color based on name
    const lowerName = name.toLowerCase();
    let color = '#CCCCCC'; // default

    for (const [key, value] of Object.entries(colors)) {
      if (lowerName.includes(key)) {
        color = value;
        break;
      }
    }

    // Fill background
    ctx.fillStyle = color;
    ctx.fillRect(0, 0, width, height);

    // Add border
    ctx.strokeStyle = '#333333';
    ctx.lineWidth = 2;
    ctx.strokeRect(1, 1, width - 2, height - 2);

    // Add text label
    ctx.fillStyle = '#FFFFFF';
    ctx.font = 'bold 12px Arial';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    // Add shadow for better readability
    ctx.fillStyle = '#000000';
    ctx.fillText(name, width / 2 + 1, height / 2 + 1);
    ctx.fillStyle = '#FFFFFF';
    ctx.fillText(name, width / 2, height / 2);

    return canvas;
  }
}

export const createPSDProcessor = (): PSDProcessor => {
  return new PSDProcessor();
};