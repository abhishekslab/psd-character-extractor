import { Slice } from '../../domain/entities/Slice';

export interface MappingRule {
  pattern: RegExp;
  slotPath: string;
  confidence: number;
}

export interface MappingResult {
  mapped: Array<{ slice: Slice; slotPath: string; confidence: number }>;
  unmapped: Slice[];
}

export class AutoMappingService {
  private rules: MappingRule[] = [
    // Mouth/Viseme mappings
    { pattern: /mouth[_ -]?a[_ -]?i?/i, slotPath: 'Mouth/viseme/AI', confidence: 0.9 },
    { pattern: /mouth[_ -]?e/i, slotPath: 'Mouth/viseme/E', confidence: 0.9 },
    { pattern: /mouth[_ -]?u/i, slotPath: 'Mouth/viseme/U', confidence: 0.9 },
    { pattern: /mouth[_ -]?o/i, slotPath: 'Mouth/viseme/O', confidence: 0.9 },
    { pattern: /mouth[_ -]?(rest|normal|neutral)/i, slotPath: 'Mouth/viseme/REST', confidence: 0.9 },
    { pattern: /mouth[_ -]?(f|v)/i, slotPath: 'Mouth/viseme/FV', confidence: 0.9 },
    { pattern: /mouth[_ -]?l/i, slotPath: 'Mouth/viseme/L', confidence: 0.9 },
    { pattern: /mouth[_ -]?(w|q)/i, slotPath: 'Mouth/viseme/WQ', confidence: 0.9 },
    { pattern: /mouth[_ -]?(m|b|p)/i, slotPath: 'Mouth/viseme/MBP', confidence: 0.9 },

    // Eye mappings
    { pattern: /eye[_ -]?l[_ -]?(open|normal)/i, slotPath: 'Eyes/EyeL/state/open', confidence: 0.9 },
    { pattern: /eye[_ -]?r[_ -]?(open|normal)/i, slotPath: 'Eyes/EyeR/state/open', confidence: 0.9 },
    { pattern: /eye[_ -]?l[_ -]?half/i, slotPath: 'Eyes/EyeL/state/half', confidence: 0.9 },
    { pattern: /eye[_ -]?r[_ -]?half/i, slotPath: 'Eyes/EyeR/state/half', confidence: 0.9 },
    { pattern: /eye[_ -]?l[_ -]?closed/i, slotPath: 'Eyes/EyeL/state/closed', confidence: 0.9 },
    { pattern: /eye[_ -]?r[_ -]?closed/i, slotPath: 'Eyes/EyeR/state/closed', confidence: 0.9 },

    // Hair mappings
    { pattern: /hair[/ _-]?(front|bangs)/i, slotPath: 'Hair/front', confidence: 0.8 },
    { pattern: /hair[/ _-]?back/i, slotPath: 'Hair/back', confidence: 0.8 },

    // Body mappings
    { pattern: /(body|torso)/i, slotPath: 'Body/torso', confidence: 0.8 },
    { pattern: /arms?/i, slotPath: 'Body/arms', confidence: 0.8 },
    { pattern: /legs?/i, slotPath: 'Body/legs', confidence: 0.8 },

    // Head mappings
    { pattern: /head[_ -]?(base|main)/i, slotPath: 'Head/base', confidence: 0.8 },
    { pattern: /neck/i, slotPath: 'Head/neck', confidence: 0.8 }
  ];

  async mapSlices(slices: Slice[]): Promise<MappingResult> {
    const mapped: Array<{ slice: Slice; slotPath: string; confidence: number }> = [];
    const unmapped: Slice[] = [];

    for (const slice of slices) {
      const mapping = this.findBestMapping(slice);
      if (mapping) {
        mapped.push({
          slice,
          slotPath: mapping.slotPath,
          confidence: mapping.confidence
        });
      } else {
        unmapped.push(slice);
      }
    }

    return { mapped, unmapped };
  }

  private findBestMapping(slice: Slice): { slotPath: string; confidence: number } | null {
    const searchTexts = [
      slice.name,
      slice.layerPath.value,
      slice.layerPath.leafName,
      slice.layerPath.value.replace(/[/_-]/g, ' ')
    ];

    let bestMatch: { slotPath: string; confidence: number } | null = null;

    for (const text of searchTexts) {
      for (const rule of this.rules) {
        if (rule.pattern.test(text)) {
          const confidence = this.calculateConfidence(text, rule);
          if (!bestMatch || confidence > bestMatch.confidence) {
            bestMatch = {
              slotPath: rule.slotPath,
              confidence
            };
          }
        }
      }
    }

    return bestMatch;
  }

  private calculateConfidence(text: string, rule: MappingRule): number {
    let confidence = rule.confidence;

    // Boost confidence for exact matches
    if (text.toLowerCase() === rule.slotPath.toLowerCase().split('/').pop()) {
      confidence = Math.min(confidence + 0.1, 1.0);
    }

    // Reduce confidence for partial path matches
    if (text.includes('/')) {
      confidence = Math.max(confidence - 0.1, 0.1);
    }

    return confidence;
  }

  addCustomRule(pattern: string, slotPath: string, confidence: number = 0.8): void {
    try {
      const regex = new RegExp(pattern, 'i');
      this.rules.push({ pattern: regex, slotPath, confidence });
    } catch (error) {
      console.warn('Invalid regex pattern:', pattern, error);
    }
  }

  learnFromMapping(slice: Slice, slotPath: string): void {
    // Create a new rule based on the slice name
    const simpleName = slice.name.toLowerCase().replace(/[^a-z0-9]/g, '');
    if (simpleName.length > 2) {
      const pattern = new RegExp(this.escapeRegex(slice.name), 'i');
      this.rules.push({
        pattern,
        slotPath,
        confidence: 0.7
      });
    }
  }

  private escapeRegex(text: string): string {
    return text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }
}