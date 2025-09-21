import { AutoMapRule, PCSRules, ExtractedSlice, SlotPalette } from '../types/avatar';

export interface MappingResult {
  slice: ExtractedSlice;
  canonicalSlot: string;
  confidence: number;
}

export class AutoMapper {
  private rules: AutoMapRule[] = [];
  private slotPalette: SlotPalette = {};

  constructor(slotPalette: SlotPalette, rules: AutoMapRule[] = []) {
    this.slotPalette = slotPalette;
    this.rules = [
      ...this.getDefaultRules(),
      ...rules
    ];
  }

  private getDefaultRules(): AutoMapRule[] {
    return [
      // Mouth/Viseme mappings
      { match: "(?i)mouth[_ -]?a[_ -]?i?", map: { group: "Mouth", slot: "Mouth/viseme/AI" } },
      { match: "(?i)mouth[_ -]?e", map: { group: "Mouth", slot: "Mouth/viseme/E" } },
      { match: "(?i)mouth[_ -]?u", map: { group: "Mouth", slot: "Mouth/viseme/U" } },
      { match: "(?i)mouth[_ -]?o", map: { group: "Mouth", slot: "Mouth/viseme/O" } },
      { match: "(?i)mouth[_ -]?(rest|normal|neutral)", map: { group: "Mouth", slot: "Mouth/viseme/REST" } },
      { match: "(?i)mouth[_ -]?(f|v)", map: { group: "Mouth", slot: "Mouth/viseme/FV" } },
      { match: "(?i)mouth[_ -]?l", map: { group: "Mouth", slot: "Mouth/viseme/L" } },
      { match: "(?i)mouth[_ -]?(w|q)", map: { group: "Mouth", slot: "Mouth/viseme/WQ" } },
      { match: "(?i)mouth[_ -]?(m|b|p)", map: { group: "Mouth", slot: "Mouth/viseme/MBP" } },
      { match: "(?i)mouth[_ -]?(sil|silent)", map: { group: "Mouth", slot: "Mouth/viseme/SIL" } },

      // Mouth/Emotion mappings
      { match: "(?i)mouth[_ -]?(smile|happy)", map: { group: "Mouth", slot: "Mouth/emotion/smile" } },
      { match: "(?i)mouth[_ -]?(frown|sad)", map: { group: "Mouth", slot: "Mouth/emotion/frown" } },
      { match: "(?i)mouth[_ -]?angry", map: { group: "Mouth", slot: "Mouth/emotion/angry" } },
      { match: "(?i)mouth[_ -]?joy", map: { group: "Mouth", slot: "Mouth/emotion/joy" } },

      // Eye mappings
      { match: "(?i)eye[_ -]?l[_ -]?(open|normal)", map: { group: "Eyes", slot: "Eyes/EyeL/state/open" } },
      { match: "(?i)eye[_ -]?r[_ -]?(open|normal)", map: { group: "Eyes", slot: "Eyes/EyeR/state/open" } },
      { match: "(?i)eye[_ -]?l[_ -]?half", map: { group: "Eyes", slot: "Eyes/EyeL/state/half" } },
      { match: "(?i)eye[_ -]?r[_ -]?half", map: { group: "Eyes", slot: "Eyes/EyeR/state/half" } },
      { match: "(?i)eye[_ -]?l[_ -]?closed", map: { group: "Eyes", slot: "Eyes/EyeL/state/closed" } },
      { match: "(?i)eye[_ -]?r[_ -]?closed", map: { group: "Eyes", slot: "Eyes/EyeR/state/closed" } },
      { match: "(?i)iris[_ -]?l", map: { group: "Eyes", slot: "Eyes/IrisL" } },
      { match: "(?i)iris[_ -]?r", map: { group: "Eyes", slot: "Eyes/IrisR" } },

      // Brow mappings
      { match: "(?i)brow[_ -]?l[_ -]?(neutral|normal)", map: { group: "Eyes", slot: "Eyes/BrowL/shape/neutral" } },
      { match: "(?i)brow[_ -]?r[_ -]?(neutral|normal)", map: { group: "Eyes", slot: "Eyes/BrowR/shape/neutral" } },
      { match: "(?i)brow[_ -]?l[_ -]?up", map: { group: "Eyes", slot: "Eyes/BrowL/shape/up" } },
      { match: "(?i)brow[_ -]?r[_ -]?up", map: { group: "Eyes", slot: "Eyes/BrowR/shape/up" } },
      { match: "(?i)brow[_ -]?l[_ -]?down", map: { group: "Eyes", slot: "Eyes/BrowL/shape/down" } },
      { match: "(?i)brow[_ -]?r[_ -]?down", map: { group: "Eyes", slot: "Eyes/BrowR/shape/down" } },
      { match: "(?i)brow[_ -]?l[_ -]?angry", map: { group: "Eyes", slot: "Eyes/BrowL/shape/angry" } },
      { match: "(?i)brow[_ -]?r[_ -]?angry", map: { group: "Eyes", slot: "Eyes/BrowR/shape/angry" } },
      { match: "(?i)brow[_ -]?l[_ -]?sad", map: { group: "Eyes", slot: "Eyes/BrowL/shape/sad" } },
      { match: "(?i)brow[_ -]?r[_ -]?sad", map: { group: "Eyes", slot: "Eyes/BrowR/shape/sad" } },

      // Hair mappings
      { match: "(?i)hair[/ _-]?(front|bangs)", map: { group: "Hair", slot: "Hair/front" } },
      { match: "(?i)hair[/ _-]?back", map: { group: "Hair", slot: "Hair/back" } },
      { match: "(?i)hair[/ _-]?mid", map: { group: "Hair", slot: "Hair/mid" } },
      { match: "(?i)hair[/ _-]?accessory", map: { group: "Hair", slot: "Hair/accessory" } },

      // Body mappings
      { match: "(?i)(body|torso)", map: { group: "Body", slot: "Body/torso" } },
      { match: "(?i)arms?", map: { group: "Body", slot: "Body/arms" } },
      { match: "(?i)legs?", map: { group: "Body", slot: "Body/legs" } },

      // Head mappings
      { match: "(?i)head[_ -]?(base|main)", map: { group: "Head", slot: "Head/base" } },
      { match: "(?i)neck", map: { group: "Head", slot: "Head/neck" } },

      // Nose mappings
      { match: "(?i)nose[_ -]?(base|main)", map: { group: "Nose", slot: "Nose/base" } },
      { match: "(?i)nose[_ -]?shadow", map: { group: "Nose", slot: "Nose/shadow" } },

      // Cheek mappings
      { match: "(?i)cheek[_ -]?blush", map: { group: "Cheek", slot: "Cheek/blush" } },
      { match: "(?i)cheek[_ -]?shadow", map: { group: "Cheek", slot: "Cheek/shadow" } },

      // Accessories mappings
      { match: "(?i)glasses", map: { group: "Accessories", slot: "Accessories/glasses" } },
      { match: "(?i)earrings?", map: { group: "Accessories", slot: "Accessories/earrings" } },
      { match: "(?i)hats?", map: { group: "Accessories", slot: "Accessories/hats" } },
      { match: "(?i)masks?", map: { group: "Accessories", slot: "Accessories/masks" } },

      // FX mappings
      { match: "(?i)sparkles?", map: { group: "FX", slot: "FX/sparkles" } },
      { match: "(?i)highlights?", map: { group: "FX", slot: "FX/highlights" } }
    ];
  }

  private normalizeSlotPath(group: string, slot: string): string {
    // Convert rule format to canonical slot format
    if (slot.includes('/')) {
      return slot;
    }

    // For slot palette entries that are arrays (like visemes)
    if (this.slotPalette[group]) {
      const groupConfig = this.slotPalette[group];

      // Find matching slot
      for (const [slotName, config] of Object.entries(groupConfig)) {
        if (Array.isArray(config) && config.includes(slot)) {
          return `${group}/${slotName}/${slot}`;
        }

        if (typeof config === 'object' && !Array.isArray(config)) {
          for (const [subKey, subValues] of Object.entries(config)) {
            if (Array.isArray(subValues) && subValues.includes(slot)) {
              return `${group}/${slotName}/${subKey}/${slot}`;
            }
          }
        }
      }
    }

    // Default format
    return `${group}/${slot}`;
  }

  mapSlices(slices: ExtractedSlice[]): { mapped: MappingResult[], unmapped: ExtractedSlice[] } {
    const mapped: MappingResult[] = [];
    const unmapped: ExtractedSlice[] = [];

    for (const slice of slices) {
      const result = this.mapSingleSlice(slice);
      if (result) {
        mapped.push(result);
        slice.mapped = true;
        slice.canonicalSlot = result.canonicalSlot;
      } else {
        unmapped.push(slice);
      }
    }

    return { mapped, unmapped };
  }

  private mapSingleSlice(slice: ExtractedSlice): MappingResult | null {
    const searchTexts = [
      slice.name,
      slice.psdPath,
      slice.psdPath.split('/').pop() || '',
      slice.psdPath.replace(/[/_-]/g, ' ')
    ];

    for (const text of searchTexts) {
      for (const rule of this.rules) {
        try {
          const regex = new RegExp(rule.match);
          if (regex.test(text)) {
            const canonicalSlot = this.normalizeSlotPath(rule.map.group, rule.map.slot);

            return {
              slice,
              canonicalSlot,
              confidence: this.calculateConfidence(text, rule)
            };
          }
        } catch (error) {
          console.warn(`Invalid regex pattern: ${rule.match}`, error);
        }
      }
    }

    return null;
  }

  private calculateConfidence(text: string, rule: AutoMapRule): number {
    // Simple confidence calculation based on match specificity
    let confidence = 0.5;

    // Exact name match gets higher confidence
    if (text.toLowerCase().includes(rule.map.slot.toLowerCase())) {
      confidence += 0.3;
    }

    // Path-based matches get slightly lower confidence
    if (text.includes('/')) {
      confidence += 0.1;
    }

    // Rule specificity (longer patterns are more specific)
    confidence += Math.min(rule.match.length / 50, 0.2);

    return Math.min(confidence, 1.0);
  }

  manualMap(slice: ExtractedSlice, canonicalSlot: string): void {
    slice.mapped = true;
    slice.canonicalSlot = canonicalSlot;

    // Learn from manual mapping
    this.learnFromMapping(slice, canonicalSlot);
  }

  private learnFromMapping(slice: ExtractedSlice, canonicalSlot: string): void {
    // Extract group and slot from canonical slot
    const parts = canonicalSlot.split('/');
    if (parts.length < 2) return;

    const group = parts[0];
    const slot = canonicalSlot;

    // Create a new rule based on the layer name
    const simpleName = slice.name.toLowerCase().replace(/[^a-z0-9]/g, '');
    if (simpleName.length > 2) {
      const newRule: AutoMapRule = {
        match: `(?i)${this.escapeRegex(slice.name)}`,
        map: { group, slot }
      };

      // Add to rules if not already present
      const exists = this.rules.some(rule =>
        rule.match === newRule.match &&
        rule.map.group === newRule.map.group &&
        rule.map.slot === newRule.map.slot
      );

      if (!exists) {
        this.rules.push(newRule);
      }
    }
  }

  private escapeRegex(text: string): string {
    return text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  getPendingRules(): AutoMapRule[] {
    // Return rules learned from manual mappings
    const defaultRuleCount = this.getDefaultRules().length;
    return this.rules.slice(defaultRuleCount);
  }

  exportRules(): PCSRules {
    return {
      aliases: this.getPendingRules()
    };
  }

  getAllAvailableSlots(): string[] {
    const slots: string[] = [];

    const processSlotConfig = (partName: string, slotName: string, config: any, prefix: string = '') => {
      const currentPrefix = prefix ? `${prefix}/${slotName}` : `${partName}/${slotName}`;

      if (Array.isArray(config)) {
        // Array of values (like visemes or emotions)
        config.forEach(value => {
          slots.push(`${currentPrefix}/${value}`);
        });
      } else if (typeof config === 'object' && config !== null && Object.keys(config).length > 0) {
        // Nested object (like Eye states)
        Object.entries(config).forEach(([subKey, subConfig]) => {
          processSlotConfig(partName, subKey, subConfig, currentPrefix);
        });
      } else {
        // Simple slot
        slots.push(currentPrefix);
      }
    };

    Object.entries(this.slotPalette).forEach(([partName, partConfig]) => {
      Object.entries(partConfig).forEach(([slotName, slotConfig]) => {
        processSlotConfig(partName, slotName, slotConfig);
      });
    });

    return slots.sort();
  }
}

export const createAutoMapper = (slotPalette: SlotPalette, customRules: AutoMapRule[] = []): AutoMapper => {
  return new AutoMapper(slotPalette, customRules);
};