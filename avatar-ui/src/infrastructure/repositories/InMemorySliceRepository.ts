import { Slice } from '../../domain/entities/Slice';
import type { SliceRepository } from '../../domain/repositories/SliceRepository';
import { SliceId } from '../../domain/value-objects/SliceId';

export class InMemorySliceRepository implements SliceRepository {
  private slices = new Map<string, Slice>();
  private mappedSliceIds = new Set<string>();

  async findById(id: SliceId): Promise<Slice | null> {
    return this.slices.get(id.value) || null;
  }

  async findAll(): Promise<Slice[]> {
    return Array.from(this.slices.values());
  }

  async save(slice: Slice): Promise<void> {
    this.slices.set(slice.id.value, slice);
  }

  async delete(id: SliceId): Promise<void> {
    this.slices.delete(id.value);
    this.mappedSliceIds.delete(id.value);
  }

  async findByLayerPath(path: string): Promise<Slice[]> {
    return Array.from(this.slices.values()).filter(
      slice => slice.layerPath.value === path
    );
  }

  async findUnmapped(): Promise<Slice[]> {
    return Array.from(this.slices.values()).filter(
      slice => !this.mappedSliceIds.has(slice.id.value)
    );
  }

  markAsMapped(id: SliceId): void {
    this.mappedSliceIds.add(id.value);
  }

  markAsUnmapped(id: SliceId): void {
    this.mappedSliceIds.delete(id.value);
  }

  clear(): void {
    this.slices.clear();
    this.mappedSliceIds.clear();
  }
}