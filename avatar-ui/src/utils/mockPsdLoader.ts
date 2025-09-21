import { ExtractedSlice } from '../types/avatar';

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

export class MockPSDProcessor {
  private canvasWidth: number = 1024;
  private canvasHeight: number = 1024;
  private fileName: string = '';

  async loadPSD(file: File): Promise<void> {
    this.fileName = file.name;
    // Simulate loading time
    await new Promise(resolve => setTimeout(resolve, 1000));
  }

  getLayerTree(): PSDLayer[] {
    // Mock layer structure for demonstration
    return [
      {
        name: 'Character',
        visible: true,
        opacity: 255,
        left: 0,
        top: 0,
        right: 1024,
        bottom: 1024,
        width: 1024,
        height: 1024,
        isGroup: true,
        path: 'Character',
        children: [
          {
            name: 'Hair',
            visible: true,
            opacity: 255,
            left: 200,
            top: 50,
            right: 800,
            bottom: 400,
            width: 600,
            height: 350,
            isGroup: true,
            path: 'Character/Hair',
            children: [
              {
                name: 'Front',
                visible: true,
                opacity: 255,
                left: 250,
                top: 100,
                right: 750,
                bottom: 300,
                width: 500,
                height: 200,
                isGroup: false,
                path: 'Character/Hair/Front'
              },
              {
                name: 'Back',
                visible: true,
                opacity: 255,
                left: 200,
                top: 50,
                right: 800,
                bottom: 400,
                width: 600,
                height: 350,
                isGroup: false,
                path: 'Character/Hair/Back'
              }
            ]
          },
          {
            name: 'Face',
            visible: true,
            opacity: 255,
            left: 300,
            top: 200,
            right: 700,
            bottom: 600,
            width: 400,
            height: 400,
            isGroup: true,
            path: 'Character/Face',
            children: [
              {
                name: 'Eyes',
                visible: true,
                opacity: 255,
                left: 350,
                top: 250,
                right: 650,
                bottom: 350,
                width: 300,
                height: 100,
                isGroup: true,
                path: 'Character/Face/Eyes',
                children: [
                  {
                    name: 'Eye L Open',
                    visible: true,
                    opacity: 255,
                    left: 370,
                    top: 270,
                    right: 450,
                    bottom: 320,
                    width: 80,
                    height: 50,
                    isGroup: false,
                    path: 'Character/Face/Eyes/Eye L Open'
                  },
                  {
                    name: 'Eye R Open',
                    visible: true,
                    opacity: 255,
                    left: 550,
                    top: 270,
                    right: 630,
                    bottom: 320,
                    width: 80,
                    height: 50,
                    isGroup: false,
                    path: 'Character/Face/Eyes/Eye R Open'
                  }
                ]
              },
              {
                name: 'Mouth',
                visible: true,
                opacity: 255,
                left: 450,
                top: 450,
                right: 550,
                bottom: 500,
                width: 100,
                height: 50,
                isGroup: true,
                path: 'Character/Face/Mouth',
                children: [
                  {
                    name: 'A',
                    visible: true,
                    opacity: 255,
                    left: 460,
                    top: 460,
                    right: 540,
                    bottom: 490,
                    width: 80,
                    height: 30,
                    isGroup: false,
                    path: 'Character/Face/Mouth/A'
                  },
                  {
                    name: 'E',
                    visible: false,
                    opacity: 255,
                    left: 465,
                    top: 465,
                    right: 535,
                    bottom: 485,
                    width: 70,
                    height: 20,
                    isGroup: false,
                    path: 'Character/Face/Mouth/E'
                  },
                  {
                    name: 'O',
                    visible: false,
                    opacity: 255,
                    left: 470,
                    top: 470,
                    right: 530,
                    bottom: 490,
                    width: 60,
                    height: 20,
                    isGroup: false,
                    path: 'Character/Face/Mouth/O'
                  }
                ]
              }
            ]
          },
          {
            name: 'Body',
            visible: true,
            opacity: 255,
            left: 250,
            top: 500,
            right: 750,
            bottom: 950,
            width: 500,
            height: 450,
            isGroup: false,
            path: 'Character/Body'
          }
        ]
      }
    ];
  }

  private createMockSliceCanvas(width: number, height: number, name: string): HTMLCanvasElement {
    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;

    const ctx = canvas.getContext('2d');
    if (!ctx) throw new Error('Could not get canvas context');

    // Create a simple colored rectangle as mock slice
    const colors = {
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

    const color = Object.keys(colors).find(key => name.includes(key)) ?
      colors[Object.keys(colors).find(key => name.includes(key))! as keyof typeof colors] : '#CCCCCC';

    ctx.fillStyle = color;
    ctx.fillRect(0, 0, width, height);

    // Add some text to identify the slice
    ctx.fillStyle = 'white';
    ctx.font = '12px Arial';
    ctx.textAlign = 'center';
    ctx.fillText(name, width / 2, height / 2);

    // Add a border
    ctx.strokeStyle = '#333';
    ctx.lineWidth = 2;
    ctx.strokeRect(0, 0, width, height);

    return canvas;
  }

  private flattenLayers(layers: PSDLayer[], parentPath: string = ''): PSDLayer[] {
    const flattened: PSDLayer[] = [];

    for (const layer of layers) {
      if (layer.children && layer.children.length > 0) {
        flattened.push(...this.flattenLayers(layer.children, layer.path));
      } else {
        if (layer.visible && layer.width > 0 && layer.height > 0) {
          flattened.push(layer);
        }
      }
    }

    return flattened;
  }

  async extractAllSlices(): Promise<ExtractedSlice[]> {
    const layerTree = this.getLayerTree();
    const flatLayers = this.flattenLayers(layerTree);
    const slices: ExtractedSlice[] = [];

    for (let i = 0; i < flatLayers.length; i++) {
      const layer = flatLayers[i];

      try {
        const canvas = this.createMockSliceCanvas(layer.width, layer.height, layer.name);
        const ctx = canvas.getContext('2d');
        if (!ctx) continue;

        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);

        const slice: ExtractedSlice = {
          id: `slice_${i.toString().padStart(3, '0')}`,
          name: layer.name,
          psdPath: layer.path,
          image: imageData,
          canvas,
          bounds: {
            x: layer.left,
            y: layer.top,
            width: layer.width,
            height: layer.height
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
    return {
      width: this.canvasWidth,
      height: this.canvasHeight
    };
  }

  async generatePreviewImage(): Promise<HTMLCanvasElement> {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');

    if (!ctx) {
      throw new Error('Could not get canvas context');
    }

    canvas.width = this.canvasWidth;
    canvas.height = this.canvasHeight;

    // Create a simple preview showing the file name
    ctx.fillStyle = '#f8f9fa';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.fillStyle = '#495057';
    ctx.font = '24px Arial';
    ctx.textAlign = 'center';
    ctx.fillText('PSD Preview', canvas.width / 2, canvas.height / 2 - 20);
    ctx.fillText(this.fileName, canvas.width / 2, canvas.height / 2 + 20);

    // Draw a simple character outline
    ctx.strokeStyle = '#007bff';
    ctx.lineWidth = 3;
    ctx.beginPath();
    // Head
    ctx.arc(canvas.width / 2, 200, 100, 0, Math.PI * 2);
    ctx.stroke();

    // Body
    ctx.beginPath();
    ctx.rect(canvas.width / 2 - 50, 300, 100, 200);
    ctx.stroke();

    return canvas;
  }
}

export const createMockPSDProcessor = (): MockPSDProcessor => {
  return new MockPSDProcessor();
};