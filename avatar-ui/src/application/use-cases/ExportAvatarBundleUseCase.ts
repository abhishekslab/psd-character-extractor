import { AvatarRepository, ExportOptions } from '../../domain/repositories/AvatarRepository';

export interface ExportAvatarBundleRequest {
  bundleName: string;
  options: ExportOptions;
}

export interface ExportAvatarBundleResponse {
  success: boolean;
  error?: string;
}

export class ExportAvatarBundleUseCase {
  constructor(
    private avatarRepository: AvatarRepository
  ) {}

  async execute(request: ExportAvatarBundleRequest): Promise<ExportAvatarBundleResponse> {
    try {
      // Get the current avatar
      const avatar = await this.avatarRepository.getCurrent();
      if (!avatar) {
        return {
          success: false,
          error: 'No avatar found to export'
        };
      }

      // Export the bundle
      const bundleBlob = await this.avatarRepository.exportBundle(avatar, request.options);

      // Trigger download
      const url = URL.createObjectURL(bundleBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${request.bundleName}_bundle_v1.zip`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      return {
        success: true
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Export failed'
      };
    }
  }
}