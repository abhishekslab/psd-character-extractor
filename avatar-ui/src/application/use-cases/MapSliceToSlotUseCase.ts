import { Avatar } from '../../domain/entities/Avatar';
import { Slice } from '../../domain/entities/Slice';
import { SliceMapping } from '../../domain/entities/SliceMapping';
import type { SliceRepository } from '../../domain/repositories/SliceRepository';
import type { AvatarRepository } from '../../domain/repositories/AvatarRepository';
import { SliceId } from '../../domain/value-objects/SliceId';
import { Bounds } from '../../domain/value-objects/Bounds';

export interface MapSliceToSlotRequest {
  sliceId: string;
  slotPath: string;
}

export interface MapSliceToSlotResponse {
  success: boolean;
  error?: string;
}

export class MapSliceToSlotUseCase {
  constructor(
    private sliceRepository: SliceRepository,
    private avatarRepository: AvatarRepository
  ) {}

  async execute(request: MapSliceToSlotRequest): Promise<MapSliceToSlotResponse> {
    try {
      // Get the current avatar
      const avatar = await this.avatarRepository.getCurrent();
      if (!avatar) {
        return {
          success: false,
          error: 'No avatar found'
        };
      }

      // Find the slice
      const sliceId = SliceId.create(request.sliceId);
      const slice = await this.sliceRepository.findById(sliceId);
      if (!slice) {
        return {
          success: false,
          error: 'Slice not found'
        };
      }

      // Create the mapping
      const mapping = new SliceMapping(
        sliceId,
        slice.bounds
      );

      // Add mapping to avatar
      avatar.addSliceMapping(request.slotPath, mapping);

      // Save the updated avatar
      await this.avatarRepository.save(avatar);

      return {
        success: true
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred'
      };
    }
  }
}