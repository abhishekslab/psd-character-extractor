import JSZip from 'jszip';
import { saveAs } from 'file-saver';
import type {
  Avatar,
  Manifest,
  PSDPathMapping,
  ExtractedSlice,
  Item,
  PCSRules
} from '../types/avatar';

export interface ExportOptions {
  includeAtlas: boolean;
  includeRawSlices: boolean;
  compressionLevel: number;
  generatePreviews: boolean;
}

export class BundleExporter {
  private avatar: Avatar;
  private mappedSlices: Record<string, ExtractedSlice>;
  private psdPathMappings: PSDPathMapping[];
  private wardrobeItems: Item[];
  private rules: PCSRules;

  constructor(
    avatar: Avatar,
    mappedSlices: Record<string, ExtractedSlice>,
    psdPathMappings: PSDPathMapping[] = [],
    wardrobeItems: Item[] = [],
    rules: PCSRules = { aliases: [] }
  ) {
    this.avatar = avatar;
    this.mappedSlices = mappedSlices;
    this.psdPathMappings = psdPathMappings;
    this.wardrobeItems = wardrobeItems;
    this.rules = rules;
  }

  async exportBundle(
    bundleName: string,
    options: ExportOptions = {
      includeAtlas: true,
      includeRawSlices: true,
      compressionLevel: 6,
      generatePreviews: true
    }
  ): Promise<void> {
    const zip = new JSZip();

    // Generate manifest
    const manifest = this.generateManifest(bundleName);
    zip.file('manifest.json', JSON.stringify(manifest, null, 2));

    // Add avatar.json
    zip.file('avatar.json', JSON.stringify(this.avatar, null, 2));

    // Add psd-paths.json
    if (this.psdPathMappings.length > 0) {
      zip.file('psd-paths.json', JSON.stringify({
        layers: this.psdPathMappings
      }, null, 2));
    }

    // Add rules
    if (this.rules.aliases.length > 0) {
      const rulesFolder = zip.folder('rules');
      if (rulesFolder) {
        const yamlContent = this.convertRulesToYAML(this.rules);
        rulesFolder.file('PCS_RULES.yaml', yamlContent);
      }
    }

    // Create slices folders
    const slicesFolder = zip.folder('slices');
    const canonFolder = slicesFolder?.folder('canon');
    const rawFolder = options.includeRawSlices ? slicesFolder?.folder('raw') : null;

    // Add canonical slices
    if (canonFolder) {
      await this.addCanonicalSlices(canonFolder);
    }

    // Add raw slices
    if (rawFolder && options.includeRawSlices) {
      await this.addRawSlices(rawFolder);
    }

    // Add atlas if requested
    if (options.includeAtlas) {
      const atlasCanvas = await this.generateAtlas();
      const atlasBlob = await this.canvasToBlob(atlasCanvas);
      zip.file('atlas.png', atlasBlob);
    }

    // Add wardrobe items
    if (this.wardrobeItems.length > 0) {
      const wardrobeFolder = zip.folder('wardrobe');
      if (wardrobeFolder) {
        await this.addWardrobeItems(wardrobeFolder);
      }
    }

    // Generate previews
    if (options.generatePreviews) {
      const previewsFolder = zip.folder('previews');
      if (previewsFolder) {
        await this.generatePreviews(previewsFolder);
      }
    }

    // Add README
    zip.file('README.txt', this.generateReadme(bundleName));

    // Generate and download the bundle
    try {
      const content = await zip.generateAsync({
        type: 'blob',
        compression: 'DEFLATE',
        compressionOptions: {
          level: options.compressionLevel
        }
      });

      saveAs(content, `${bundleName}_bundle_v1.zip`);
    } catch (error) {
      console.error('Error generating bundle:', error);
      throw new Error('Failed to generate bundle');
    }
  }

  private generateManifest(bundleName: string): Manifest {
    const hashes: Record<string, string> = {};

    // Calculate sample hashes (in a real implementation, you'd calculate actual hashes)
    Object.keys(this.mappedSlices).forEach(slotPath => {
      const fileName = this.getCanonicalFileName(slotPath);
      hashes[`slices/canon/${fileName}`] = this.generateSampleHash();
    });

    return {
      name: bundleName,
      version: '1.0.0',
      schema: {
        avatar: '1.0.0',
        bundle: '1.0.0'
      },
      entry: {
        avatar: 'avatar.json'
      },
      rigId: this.avatar.meta.rigId || 'anime-1024-headA-v1',
      fitBoxes: {
        hair: { x: 280, y: 40, w: 460, h: 520 },
        top: { x: 240, y: 380, w: 520, h: 420 },
        accessories: { x: 200, y: 100, w: 600, h: 800 }
      },
      hashes
    };
  }

  private async addCanonicalSlices(canonFolder: JSZip): Promise<void> {
    for (const [slotPath, slice] of Object.entries(this.mappedSlices)) {
      const fileName = this.getCanonicalFileName(slotPath);
      const folderPath = this.getCanonicalFolderPath(slotPath);

      // Create nested folder structure
      const targetFolder = this.ensureFolder(canonFolder, folderPath);

      // Convert canvas to blob and add to zip
      const blob = await this.canvasToBlob(slice.canvas);
      targetFolder.file(fileName, blob);
    }
  }

  private async addRawSlices(rawFolder: JSZip): Promise<void> {
    for (const slice of Object.values(this.mappedSlices)) {
      const pathParts = slice.psdPath.split('/');
      const fileName = `${pathParts[pathParts.length - 1]}.png`;
      const folderPath = pathParts.slice(0, -1).join('/');

      // Create nested folder structure
      const targetFolder = this.ensureFolder(rawFolder, folderPath);

      // Convert canvas to blob and add to zip
      const blob = await this.canvasToBlob(slice.canvas);
      targetFolder.file(fileName, blob);
    }
  }

  private async addWardrobeItems(wardrobeFolder: JSZip): Promise<void> {
    for (const item of this.wardrobeItems) {
      const typeFolder = wardrobeFolder.folder(item.type);
      const itemFolder = typeFolder?.folder(item.sku);

      if (itemFolder) {
        // Add item.json
        itemFolder.file('item.json', JSON.stringify(item, null, 2));

        // Add item slices
        for (const [slotPath, fileName] of Object.entries(item.slices)) {
          const slice = this.mappedSlices[slotPath];
          if (slice) {
            const blob = await this.canvasToBlob(slice.canvas);
            itemFolder.file(fileName, blob);
          }
        }
      }
    }
  }

  private async generatePreviews(previewsFolder: JSZip): Promise<void> {
    // Generate main avatar preview
    const avatarPreview = await this.generateAvatarPreview();
    const avatarBlob = await this.canvasToBlob(avatarPreview);
    previewsFolder.file('avatar.png', avatarBlob);

    // Generate individual wardrobe item previews
    for (const item of this.wardrobeItems) {
      const itemPreview = await this.generateItemPreview(item);
      if (itemPreview) {
        const itemBlob = await this.canvasToBlob(itemPreview);
        previewsFolder.file(`${item.type}_${item.sku}.png`, itemBlob);
      }
    }
  }

  private async generateAtlas(): Promise<HTMLCanvasElement> {
    // Calculate optimal atlas dimensions
    const slices = Object.values(this.mappedSlices);
    const totalArea = slices.reduce((sum, slice) =>
      sum + slice.bounds.width * slice.bounds.height, 0
    );

    const atlasSize = Math.ceil(Math.sqrt(totalArea * 1.2)); // 20% padding
    const canvas = document.createElement('canvas');
    canvas.width = Math.min(atlasSize, 4096); // Max 4K atlas
    canvas.height = Math.min(atlasSize, 4096);

    const ctx = canvas.getContext('2d');
    if (!ctx) throw new Error('Could not get canvas context');

    // Simple bin packing algorithm
    let currentX = 0;
    let currentY = 0;
    let rowHeight = 0;

    for (const [slotPath, slice] of Object.entries(this.mappedSlices)) {
      const sliceWidth = slice.bounds.width;
      const sliceHeight = slice.bounds.height;

      // Check if we need a new row
      if (currentX + sliceWidth > canvas.width) {
        currentX = 0;
        currentY += rowHeight;
        rowHeight = 0;
      }

      // Draw slice to atlas
      ctx.drawImage(slice.canvas, currentX, currentY);

      // Update avatar slice info with atlas coordinates
      if (this.avatar.images.slices[slotPath]) {
        this.avatar.images.slices[slotPath] = {
          ...this.avatar.images.slices[slotPath],
          x: currentX,
          y: currentY,
          w: sliceWidth,
          h: sliceHeight
        };
      }

      currentX += sliceWidth;
      rowHeight = Math.max(rowHeight, sliceHeight);
    }

    // Update avatar to reference atlas
    this.avatar.images.atlas = 'atlas.png';

    return canvas;
  }

  private async generateAvatarPreview(): Promise<HTMLCanvasElement> {
    const canvas = document.createElement('canvas');
    canvas.width = 512;
    canvas.height = 512;
    const ctx = canvas.getContext('2d');

    if (!ctx) throw new Error('Could not get canvas context');

    // Draw slices in draw order
    const sortedSlices = Object.entries(this.mappedSlices).sort(([a], [b]) => {
      const indexA = this.avatar.drawOrder.findIndex(pattern =>
        pattern.includes('*') ? a.startsWith(pattern.replace('/*', '')) : a === pattern
      );
      const indexB = this.avatar.drawOrder.findIndex(pattern =>
        pattern.includes('*') ? b.startsWith(pattern.replace('/*', '')) : b === pattern
      );
      return indexA - indexB;
    });

    for (const [slotPath, slice] of sortedSlices) {
      const scale = Math.min(
        canvas.width / 1024,
        canvas.height / 1024
      );

      ctx.drawImage(
        slice.canvas,
        slice.bounds.x * scale,
        slice.bounds.y * scale,
        slice.bounds.width * scale,
        slice.bounds.height * scale
      );
    }

    return canvas;
  }

  private async generateItemPreview(item: Item): Promise<HTMLCanvasElement | null> {
    const relevantSlices = item.fills
      .map(slotPath => this.mappedSlices[slotPath])
      .filter(Boolean);

    if (relevantSlices.length === 0) return null;

    const canvas = document.createElement('canvas');
    canvas.width = 256;
    canvas.height = 256;
    const ctx = canvas.getContext('2d');

    if (!ctx) return null;

    // Calculate bounding box
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;

    for (const slice of relevantSlices) {
      minX = Math.min(minX, slice.bounds.x);
      minY = Math.min(minY, slice.bounds.y);
      maxX = Math.max(maxX, slice.bounds.x + slice.bounds.width);
      maxY = Math.max(maxY, slice.bounds.y + slice.bounds.height);
    }

    const boundingWidth = maxX - minX;
    const boundingHeight = maxY - minY;
    const scale = Math.min(canvas.width / boundingWidth, canvas.height / boundingHeight) * 0.8;

    const offsetX = (canvas.width - boundingWidth * scale) / 2;
    const offsetY = (canvas.height - boundingHeight * scale) / 2;

    for (const slice of relevantSlices) {
      ctx.drawImage(
        slice.canvas,
        (slice.bounds.x - minX) * scale + offsetX,
        (slice.bounds.y - minY) * scale + offsetY,
        slice.bounds.width * scale,
        slice.bounds.height * scale
      );
    }

    return canvas;
  }

  private convertRulesToYAML(rules: PCSRules): string {
    let yaml = 'aliases:\n';

    for (const rule of rules.aliases) {
      yaml += `  - match: "${rule.match}"\n`;
      yaml += `    map:\n`;
      yaml += `      group: ${rule.map.group}\n`;
      yaml += `      slot: "${rule.map.slot}"\n`;
    }

    return yaml;
  }

  private generateReadme(bundleName: string): string {
    return `# ${bundleName} Avatar Bundle

This bundle contains a complete avatar definition with slices, mappings, and metadata.

## Contents

- manifest.json: Bundle metadata and configuration
- avatar.json: Avatar definition with slots and draw order
- slices/canon/: Canonical slices organized by slot
- slices/raw/: Original PSD layer organization
- rules/PCS_RULES.yaml: Auto-mapping rules learned from this PSD
- wardrobe/: Interchangeable items organized by type
- previews/: Preview images for avatar and items
- atlas.png: Texture atlas (if included)

## Usage

Load this bundle in compatible avatar systems that support the Avatar Bundle v1.0.0 specification.

Generated by PSD Character Extractor Avatar UI
${new Date().toISOString()}
`;
  }

  private getCanonicalFileName(slotPath: string): string {
    const parts = slotPath.split('/');
    return `${parts[parts.length - 1]}.png`;
  }

  private getCanonicalFolderPath(slotPath: string): string {
    const parts = slotPath.split('/');
    return parts.slice(0, -1).join('/');
  }

  private ensureFolder(parent: JSZip, path: string): JSZip {
    if (!path) return parent;

    const parts = path.split('/').filter(Boolean);
    let current = parent;

    for (const part of parts) {
      current = current.folder(part) || current;
    }

    return current;
  }

  private async canvasToBlob(canvas: HTMLCanvasElement): Promise<Blob> {
    return new Promise((resolve, reject) => {
      canvas.toBlob((blob) => {
        if (blob) {
          resolve(blob);
        } else {
          reject(new Error('Failed to convert canvas to blob'));
        }
      }, 'image/png');
    });
  }

  private generateSampleHash(): string {
    // Generate a sample SHA-256 hash
    const chars = '0123456789abcdef';
    let hash = 'sha256-';
    for (let i = 0; i < 64; i++) {
      hash += chars[Math.floor(Math.random() * chars.length)];
    }
    return hash;
  }
}

export const createBundleExporter = (
  avatar: Avatar,
  mappedSlices: Record<string, ExtractedSlice>,
  psdPathMappings?: PSDPathMapping[],
  wardrobeItems?: Item[],
  rules?: PCSRules
): BundleExporter => {
  return new BundleExporter(avatar, mappedSlices, psdPathMappings, wardrobeItems, rules);
};