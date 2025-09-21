import { Slice } from '../entities/Slice';
import { SliceId } from '../value-objects/SliceId';

export interface SliceRepository {
  findById(id: SliceId): Promise<Slice | null>;
  findAll(): Promise<Slice[]>;
  save(slice: Slice): Promise<void>;
  delete(id: SliceId): Promise<void>;
  findByLayerPath(path: string): Promise<Slice[]>;
  findUnmapped(): Promise<Slice[]>;
}