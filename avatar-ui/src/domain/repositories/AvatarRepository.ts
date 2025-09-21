import { Avatar } from '../entities/Avatar';

export interface AvatarRepository {
  getCurrent(): Promise<Avatar | null>;
  save(avatar: Avatar): Promise<void>;
  exportBundle(avatar: Avatar, options: ExportOptions): Promise<Blob>;
}

export interface ExportOptions {
  includeAtlas: boolean;
  includeRawSlices: boolean;
  compressionLevel: number;
  generatePreviews: boolean;
}