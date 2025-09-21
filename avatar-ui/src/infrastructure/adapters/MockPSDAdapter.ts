import { PSDRepository, PSDDocument } from '../../domain/repositories/PSDRepository';
import { Slice } from '../../domain/entities/Slice';
import { SliceId } from '../../domain/value-objects/SliceId';
import { LayerPath } from '../../domain/value-objects/LayerPath';
import { Bounds } from '../../domain/value-objects/Bounds';

interface MockLayer {
  name: string;
  path: string;
  bounds: { x: number; y: number; width: number; height: number };
  children?: MockLayer[];
}

export class MockPSDAdapter implements PSDRepository {
  async loadFromFile(file: File): Promise<PSDDocument> {
    // Simulate loading time
    await new Promise(resolve => setTimeout(resolve, 1000));

    return {
      width: 1024,
      height: 1024,
      filename: file.name,
      layerCount: 8
    };
  }

  async extractSlices(document: PSDDocument): Promise<Slice[]> {
    // Simulate extraction time
    await new Promise(resolve => setTimeout(resolve, 500));

    const mockLayers = this.getMockLayers();
    const flatLayers = this.flattenLayers(mockLayers);
    const slices: Slice[] = [];

    for (let i = 0; i < flatLayers.length; i++) {
      const layer = flatLayers[i];
      const canvas = this.createMockCanvas(layer.bounds.width, layer.bounds.height, layer.name);
      const ctx = canvas.getContext('2d')!;
      const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);

      const slice = new Slice(
        SliceId.generate(i),
        layer.name,
        LayerPath.create(layer.path),
        Bounds.create(layer.bounds.x, layer.bounds.y, layer.bounds.width, layer.bounds.height),
        canvas,
        imageData
      );

      slices.push(slice);
    }

    return slices;
  }

  private getMockLayers(): MockLayer[] {
    return [
      {
        name: 'Hair',
        path: 'Character/Hair',
        bounds: { x: 200, y: 50, width: 600, height: 350 },
        children: [
          {
            name: 'Front',
            path: 'Character/Hair/Front',
            bounds: { x: 250, y: 100, width: 500, height: 200 }
          },
          {
            name: 'Back',
            path: 'Character/Hair/Back',
            bounds: { x: 200, y: 50, width: 600, height: 350 }
          }
        ]
      },
      {
        name: 'Face',
        path: 'Character/Face',
        bounds: { x: 300, y: 200, width: 400, height: 400 },
        children: [
          {
            name: 'Eyes',
            path: 'Character/Face/Eyes',
            bounds: { x: 350, y: 250, width: 300, height: 100 },
            children: [
              {
                name: 'Eye L Open',
                path: 'Character/Face/Eyes/Eye L Open',
                bounds: { x: 370, y: 270, width: 80, height: 50 }
              },
              {
                name: 'Eye R Open',
                path: 'Character/Face/Eyes/Eye R Open',
                bounds: { x: 550, y: 270, width: 80, height: 50 }
              }
            ]
          },
          {
            name: 'Mouth',
            path: 'Character/Face/Mouth',
            bounds: { x: 450, y: 450, width: 100, height: 50 },
            children: [
              {
                name: 'A',
                path: 'Character/Face/Mouth/A',
                bounds: { x: 460, y: 460, width: 80, height: 30 }
              },
              {
                name: 'E',
                path: 'Character/Face/Mouth/E',
                bounds: { x: 465, y: 465, width: 70, height: 20 }
              },
              {
                name: 'O',
                path: 'Character/Face/Mouth/O',
                bounds: { x: 470, y: 470, width: 60, height: 20 }
              }
            ]
          }
        ]
      },
      {
        name: 'Body',
        path: 'Character/Body',
        bounds: { x: 250, y: 500, width: 500, height: 450 }
      }
    ];
  }

  private flattenLayers(layers: MockLayer[]): MockLayer[] {
    const flattened: MockLayer[] = [];

    for (const layer of layers) {
      if (layer.children && layer.children.length > 0) {
        flattened.push(...this.flattenLayers(layer.children));
      } else {
        flattened.push(layer);
      }
    }

    return flattened;
  }

  private createMockCanvas(width: number, height: number, name: string): HTMLCanvasElement {
    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;

    const ctx = canvas.getContext('2d')!;

    // Create a simple colored rectangle as mock slice
    const colors: Record<string, string> = {
      'Hair': '#8B4513',
      'Eye': '#4169E1',
      'Mouth': '#FF6B6B',
      'Body': '#FFB6C1',
      'Front': '#DEB887',
      'Back': '#CD853F',
      'A': '#FF4500',
      'E': '#FF6347',
      'O': '#FF7F50'
    };

    const color = Object.keys(colors).find(key => name.includes(key));
    ctx.fillStyle = color ? colors[color] : '#CCCCCC';
    ctx.fillRect(0, 0, width, height);

    // Add text label
    ctx.fillStyle = 'white';
    ctx.font = '12px Arial';
    ctx.textAlign = 'center';
    ctx.fillText(name, width / 2, height / 2);

    // Add border
    ctx.strokeStyle = '#333';
    ctx.lineWidth = 2;
    ctx.strokeRect(0, 0, width, height);

    return canvas;
  }
}