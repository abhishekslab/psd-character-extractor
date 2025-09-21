import type { PSDRepository, PSDDocument } from '../../domain/repositories/PSDRepository';
import { Slice } from '../../domain/entities/Slice';
import { SliceId } from '../../domain/value-objects/SliceId';
import { LayerPath } from '../../domain/value-objects/LayerPath';
import { Bounds } from '../../domain/value-objects/Bounds';
import { PSDProcessor } from '../../utils/robustPsdLoader';

export class PSDAdapter implements PSDRepository {
  private psdProcessor: PSDProcessor;

  constructor() {
    this.psdProcessor = new PSDProcessor();
  }

  async loadFromFile(file: File): Promise<PSDDocument> {
    try {
      console.log('PSDAdapter: Loading PSD file:', file.name);

      await this.psdProcessor.loadPSD(file);
      console.log('PSDAdapter: PSD loaded successfully');

      const dimensions = this.psdProcessor.getPSDDimensions();
      console.log('PSDAdapter: Got dimensions:', dimensions);

      const layerTree = this.psdProcessor.getLayerTree();
      console.log('PSDAdapter: Got layer tree:', layerTree);
      console.log('PSDAdapter: Layer tree type:', typeof layerTree, 'isArray:', Array.isArray(layerTree));

      const layerCount = this.countLayers(layerTree);
      console.log('PSDAdapter: Counted layers:', layerCount);

      return {
        width: dimensions.width,
        height: dimensions.height,
        filename: file.name,
        layerCount
      };
    } catch (error) {
      console.error('Failed to load PSD file:', error);
      throw new Error(`Failed to load PSD file: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async extractSlices(document: PSDDocument): Promise<Slice[]> {
    try {
      const extractedSlices = await this.psdProcessor.extractAllSlices();
      const slices: Slice[] = [];

      for (let i = 0; i < extractedSlices.length; i++) {
        const extractedSlice = extractedSlices[i];

        const slice = new Slice(
          SliceId.create(extractedSlice.id),
          extractedSlice.name,
          LayerPath.create(extractedSlice.psdPath),
          Bounds.create(
            extractedSlice.bounds.x,
            extractedSlice.bounds.y,
            extractedSlice.bounds.width,
            extractedSlice.bounds.height
          ),
          extractedSlice.canvas,
          extractedSlice.image
        );

        slices.push(slice);
      }

      return slices;
    } catch (error) {
      console.error('Failed to extract slices:', error);
      throw new Error(`Failed to extract slices: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }


  private countLayers(layerTree: any): number {
    if (!layerTree || !Array.isArray(layerTree)) {
      return 0;
    }

    let count = 0;
    for (const layer of layerTree) {
      count++;
      if (layer && layer.children && Array.isArray(layer.children)) {
        count += this.countLayers(layer.children);
      }
    }
    return count;
  }
}