import type { PSDRepository } from '../../domain/repositories/PSDRepository';
import type { SliceRepository } from '../../domain/repositories/SliceRepository';
import { AutoMappingService } from '../services/AutoMappingService';

export interface LoadPSDRequest {
  file: File;
}

export interface LoadPSDResponse {
  success: boolean;
  extractedSlicesCount: number;
  autoMappedCount: number;
  unmappedCount: number;
  error?: string;
}

export class LoadPSDUseCase {
  constructor(
    private psdRepository: PSDRepository,
    private sliceRepository: SliceRepository,
    private autoMappingService: AutoMappingService
  ) {}

  async execute(request: LoadPSDRequest): Promise<LoadPSDResponse> {
    try {
      // Load PSD document
      const psdDocument = await this.psdRepository.loadFromFile(request.file);

      // Extract slices from the document
      const slices = await this.psdRepository.extractSlices(psdDocument);

      // Save all slices to repository
      await Promise.all(slices.map(slice => this.sliceRepository.save(slice)));

      // Perform auto-mapping
      const mappingResult = await this.autoMappingService.mapSlices(slices);

      return {
        success: true,
        extractedSlicesCount: slices.length,
        autoMappedCount: mappingResult.mapped.length,
        unmappedCount: mappingResult.unmapped.length
      };
    } catch (error) {
      return {
        success: false,
        extractedSlicesCount: 0,
        autoMappedCount: 0,
        unmappedCount: 0,
        error: error instanceof Error ? error.message : 'Unknown error occurred'
      };
    }
  }
}