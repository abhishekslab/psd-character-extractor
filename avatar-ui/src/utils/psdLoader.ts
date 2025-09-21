import PSD from 'psd.js';
import type { ExtractedSlice } from '../types/avatar';

export interface PSDLayer {
  name: string;
  visible: boolean;
  opacity: number;
  left: number;
  top: number;
  right: number;
  bottom: number;
  width: number;
  height: number;
  children?: PSDLayer[];
  isGroup: boolean;
  path: string;
}

export class PSDProcessor {
  private psd: any;
  private canvasWidth: number = 1024;
  private canvasHeight: number = 1024;

  async loadPSD(file: File): Promise<void> {
    const arrayBuffer = await file.arrayBuffer();
    const buffer = new Uint8Array(arrayBuffer);
    this.psd = new PSD(buffer);
    this.psd.parse();
  }

  private buildLayerPath(layer: any, parentPath: string = ''): string {
    const name = layer.name ? layer.name() : 'Unnamed';
    return parentPath ? `${parentPath}/${name}` : name;
  }

  private extractLayerInfo(layer: any, parentPath: string = ''): PSDLayer {
    const path = this.buildLayerPath(layer, parentPath);
    const name = layer.name ? layer.name() : 'Unnamed';
    const left = layer.left ? layer.left() : 0;
    const top = layer.top ? layer.top() : 0;
    const right = layer.right ? layer.right() : 0;
    const bottom = layer.bottom ? layer.bottom() : 0;

    return {
      name,
      visible: layer.visible ? layer.visible() : true,
      opacity: layer.opacity ? layer.opacity() : 255,
      left,
      top,
      right,
      bottom,
      width: right - left,
      height: bottom - top,
      isGroup: layer.children ? layer.children().length > 0 : false,
      path,
      children: layer.children ? layer.children().map((child: any) =>
        this.extractLayerInfo(child, path)
      ) : undefined
    };
  }

  getLayerTree(): PSDLayer[] {
    if (!this.psd || !this.psd.tree()) {
      return [];
    }

    return this.psd.tree().children().map((layer: any) =>
      this.extractLayerInfo(layer)
    );
  }

  private async renderLayerToCanvas(layer: any): Promise<HTMLCanvasElement | null> {
    try {
      const width = layer.width || 0;
      const height = layer.height || 0;

      // Skip if layer has no content or is empty
      if (!layer || width <= 0 || height <= 0) {
        return null;
      }

      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');

      if (!ctx) {
        throw new Error('Could not get canvas context');
      }

      canvas.width = width;
      canvas.height = height;

      // Get layer image data using the correct API
      const imageData = layer.toPng ? layer.toPng() : null;
      if (!imageData) {
        return null;
      }

      // Create image from blob
      const blob = new Blob([imageData], { type: 'image/png' });
      const img = new Image();

      return new Promise((resolve, reject) => {
        img.onload = () => {
          ctx.drawImage(img, 0, 0);
          resolve(canvas);
        };
        img.onerror = () => reject(new Error('Failed to load layer image'));
        img.src = URL.createObjectURL(blob);
      });
    } catch (error) {
      console.error('Error rendering layer to canvas:', error);
      return null;
    }
  }

  private flattenLayers(layers: any[], parentPath: string = ''): any[] {
    const flattened: any[] = [];

    for (const layer of layers) {
      const path = this.buildLayerPath(layer, parentPath);
      const children = layer.children ? layer.children() : [];
      const visible = layer.visible ? layer.visible() : true;
      const width = layer.width || 0;
      const height = layer.height || 0;

      if (children && children.length > 0) {
        // If it's a group, recurse into children
        flattened.push(...this.flattenLayers(children, path));
      } else {
        // If it's a leaf layer and visible, add it
        if (visible && width > 0 && height > 0) {
          flattened.push({
            ...layer,
            path,
            width,
            height,
            visible,
            name: layer.name ? layer.name() : 'Unnamed',
            left: layer.left ? layer.left() : 0,
            top: layer.top ? layer.top() : 0
          });
        }
      }
    }

    return flattened;
  }

  async extractAllSlices(): Promise<ExtractedSlice[]> {
    if (!this.psd || !this.psd.tree()) {
      throw new Error('No PSD loaded');
    }

    const flatLayers = this.flattenLayers(this.psd.tree().children());
    const slices: ExtractedSlice[] = [];

    for (let i = 0; i < flatLayers.length; i++) {
      const layer = flatLayers[i];

      try {
        const canvas = await this.renderLayerToCanvas(layer);
        if (!canvas) {
          continue;
        }

        const ctx = canvas.getContext('2d');
        if (!ctx) {
          continue;
        }

        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);

        const slice: ExtractedSlice = {
          id: `slice_${i.toString().padStart(3, '0')}`,
          name: layer.name || 'Unnamed',
          psdPath: layer.path,
          image: imageData,
          canvas,
          bounds: {
            x: layer.left || 0,
            y: layer.top || 0,
            width: layer.width || 0,
            height: layer.height || 0
          },
          mapped: false
        };

        slices.push(slice);
      } catch (error) {
        console.error(`Error extracting slice for layer ${layer.name}:`, error);
      }
    }

    return slices;
  }

  getPSDDimensions(): { width: number; height: number } {
    if (!this.psd) {
      return { width: this.canvasWidth, height: this.canvasHeight };
    }

    return {
      width: this.psd.header ? (this.psd.header.width || this.canvasWidth) : this.canvasWidth,
      height: this.psd.header ? (this.psd.header.height || this.canvasHeight) : this.canvasHeight
    };
  }

  async generatePreviewImage(): Promise<HTMLCanvasElement> {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');

    if (!ctx) {
      throw new Error('Could not get canvas context');
    }

    const dimensions = this.getPSDDimensions();
    canvas.width = dimensions.width;
    canvas.height = dimensions.height;

    if (this.psd) {
      try {
        const imageData = this.psd.image.toPng();
        const blob = new Blob([imageData], { type: 'image/png' });
        const img = new Image();

        return new Promise((resolve, reject) => {
          img.onload = () => {
            ctx.drawImage(img, 0, 0);
            resolve(canvas);
          };
          img.onerror = () => reject(new Error('Failed to load PSD preview'));
          img.src = URL.createObjectURL(blob);
        });
      } catch (error) {
        console.error('Error generating preview:', error);
      }
    }

    // Return empty canvas if preview generation fails
    return canvas;
  }
}

export const createPSDProcessor = (): PSDProcessor => {
  return new PSDProcessor();
};