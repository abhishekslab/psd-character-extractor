import { useState, useCallback } from 'react';
import { Container } from '../../infrastructure/di/Container';
import { Slice } from '../../domain/entities/Slice';
import { Avatar } from '../../domain/entities/Avatar';

interface AvatarAssemblyState {
  avatar: Avatar | null;
  allSlices: Slice[];
  unmappedSlices: Slice[];
  mappedSlices: Slice[];
  selectedSlot: string | null;
  isProcessing: boolean;
  error: string | null;
}

export const useAvatarAssembly = () => {
  const [state, setState] = useState<AvatarAssemblyState>({
    avatar: null,
    allSlices: [],
    unmappedSlices: [],
    mappedSlices: [],
    selectedSlot: null,
    isProcessing: false,
    error: null
  });

  const container = Container.getInstance();
  const loadPSDUseCase = container.getLoadPSDUseCase();
  const mapSliceUseCase = container.getMapSliceToSlotUseCase();
  const exportUseCase = container.getExportAvatarBundleUseCase();
  const sliceRepository = container.getSliceRepository();
  const avatarRepository = container.getAvatarRepository();

  const loadPSD = useCallback(async (file: File) => {
    setState(prev => ({ ...prev, isProcessing: true, error: null }));

    try {
      const result = await loadPSDUseCase.execute({ file });

      if (result.success) {
        // Refresh data from repositories
        const allSlices = await sliceRepository.findAll();
        const unmappedSlices = await sliceRepository.findUnmapped();
        const mappedSlices = allSlices.filter(slice =>
          !unmappedSlices.some(unmapped => unmapped.id.equals(slice.id))
        );
        const avatar = await avatarRepository.getCurrent();

        setState(prev => ({
          ...prev,
          avatar,
          allSlices,
          unmappedSlices,
          mappedSlices,
          isProcessing: false
        }));
      } else {
        setState(prev => ({
          ...prev,
          error: result.error || 'Failed to load PSD',
          isProcessing: false
        }));
      }
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Unknown error',
        isProcessing: false
      }));
    }
  }, [loadPSDUseCase, sliceRepository, avatarRepository]);

  const mapSliceToSlot = useCallback(async (sliceId: string, slotPath: string) => {
    try {
      const result = await mapSliceUseCase.execute({ sliceId, slotPath });

      if (result.success) {
        // Refresh data
        const allSlices = await sliceRepository.findAll();
        const unmappedSlices = await sliceRepository.findUnmapped();
        const mappedSlices = allSlices.filter(slice =>
          !unmappedSlices.some(unmapped => unmapped.id.equals(slice.id))
        );
        const avatar = await avatarRepository.getCurrent();

        setState(prev => ({
          ...prev,
          avatar,
          allSlices,
          unmappedSlices,
          mappedSlices,
          selectedSlot: slotPath
        }));

        // Mark slice as mapped in repository
        const sliceRepo = container.getSliceRepository() as any;
        if (sliceRepo.markAsMapped) {
          const slice = allSlices.find(s => s.id.value === sliceId);
          if (slice) {
            sliceRepo.markAsMapped(slice.id);
          }
        }
      } else {
        setState(prev => ({
          ...prev,
          error: result.error || 'Failed to map slice'
        }));
      }
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Unknown error'
      }));
    }
  }, [mapSliceUseCase, sliceRepository, avatarRepository, container]);

  const exportBundle = useCallback(async (bundleName: string = 'Avatar') => {
    try {
      const result = await exportUseCase.execute({
        bundleName,
        options: {
          includeAtlas: true,
          includeRawSlices: true,
          compressionLevel: 6,
          generatePreviews: true
        }
      });

      if (!result.success) {
        setState(prev => ({
          ...prev,
          error: result.error || 'Failed to export bundle'
        }));
      }
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Unknown error'
      }));
    }
  }, [exportUseCase]);

  const selectSlot = useCallback((slotPath: string) => {
    setState(prev => ({ ...prev, selectedSlot: slotPath }));
  }, []);

  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: null }));
  }, []);

  return {
    // State
    avatar: state.avatar,
    allSlices: state.allSlices,
    unmappedSlices: state.unmappedSlices,
    mappedSlices: state.mappedSlices,
    selectedSlot: state.selectedSlot,
    isProcessing: state.isProcessing,
    error: state.error,

    // Actions
    loadPSD,
    mapSliceToSlot,
    exportBundle,
    selectSlot,
    clearError
  };
};