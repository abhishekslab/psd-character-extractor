// Dependency Injection Container
import type { PSDRepository } from '../../domain/repositories/PSDRepository';
import type { SliceRepository } from '../../domain/repositories/SliceRepository';
import type { AvatarRepository } from '../../domain/repositories/AvatarRepository';

import { AutoMappingService } from '../../application/services/AutoMappingService';
import { LoadPSDUseCase } from '../../application/use-cases/LoadPSDUseCase';
import { MapSliceToSlotUseCase } from '../../application/use-cases/MapSliceToSlotUseCase';
import { ExportAvatarBundleUseCase } from '../../application/use-cases/ExportAvatarBundleUseCase';

import { PSDAdapter } from '../adapters/PSDAdapter';
import { InMemorySliceRepository } from '../repositories/InMemorySliceRepository';
import { InMemoryAvatarRepository } from '../repositories/InMemoryAvatarRepository';

export class Container {
  private static instance: Container;
  private dependencies = new Map<string, any>();

  private constructor() {
    this.configureDependencies();
  }

  static getInstance(): Container {
    if (!Container.instance) {
      Container.instance = new Container();
    }
    return Container.instance;
  }

  private configureDependencies(): void {
    // Repositories
    this.dependencies.set('PSDRepository', new PSDAdapter());
    this.dependencies.set('SliceRepository', new InMemorySliceRepository());
    this.dependencies.set('AvatarRepository', new InMemoryAvatarRepository());

    // Services
    this.dependencies.set('AutoMappingService', new AutoMappingService());

    // Use Cases
    this.dependencies.set('LoadPSDUseCase', new LoadPSDUseCase(
      this.get<PSDRepository>('PSDRepository'),
      this.get<SliceRepository>('SliceRepository'),
      this.get<AutoMappingService>('AutoMappingService')
    ));

    this.dependencies.set('MapSliceToSlotUseCase', new MapSliceToSlotUseCase(
      this.get<SliceRepository>('SliceRepository'),
      this.get<AvatarRepository>('AvatarRepository')
    ));

    this.dependencies.set('ExportAvatarBundleUseCase', new ExportAvatarBundleUseCase(
      this.get<AvatarRepository>('AvatarRepository')
    ));
  }

  get<T>(key: string): T {
    const dependency = this.dependencies.get(key);
    if (!dependency) {
      throw new Error(`Dependency not found: ${key}`);
    }
    return dependency;
  }

  // Convenience methods for common dependencies
  getLoadPSDUseCase(): LoadPSDUseCase {
    return this.get<LoadPSDUseCase>('LoadPSDUseCase');
  }

  getMapSliceToSlotUseCase(): MapSliceToSlotUseCase {
    return this.get<MapSliceToSlotUseCase>('MapSliceToSlotUseCase');
  }

  getExportAvatarBundleUseCase(): ExportAvatarBundleUseCase {
    return this.get<ExportAvatarBundleUseCase>('ExportAvatarBundleUseCase');
  }

  getSliceRepository(): SliceRepository {
    return this.get<SliceRepository>('SliceRepository');
  }

  getAvatarRepository(): AvatarRepository {
    return this.get<AvatarRepository>('AvatarRepository');
  }

  getAutoMappingService(): AutoMappingService {
    return this.get<AutoMappingService>('AutoMappingService');
  }
}