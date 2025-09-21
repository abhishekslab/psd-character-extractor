import { Slice } from '../entities/Slice';

export interface PSDRepository {
  loadFromFile(file: File): Promise<PSDDocument>;
  extractSlices(document: PSDDocument): Promise<Slice[]>;
}

export interface PSDDocument {
  width: number;
  height: number;
  filename: string;
  layerCount: number;
}