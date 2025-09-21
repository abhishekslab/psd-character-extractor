import Ajv, { JSONSchemaType } from 'ajv';
import { Avatar, Manifest, Item } from '../types/avatar';

// Avatar JSON Schema
export const avatarSchema: JSONSchemaType<Avatar> = {
  type: 'object',
  properties: {
    meta: {
      type: 'object',
      properties: {
        generator: { type: 'string' },
        rigId: { type: 'string' }
      },
      required: ['generator', 'rigId'],
      additionalProperties: true
    },
    images: {
      type: 'object',
      properties: {
        atlas: { type: 'string', nullable: true },
        slices: {
          type: 'object',
          patternProperties: {
            '.*': {
              type: 'object',
              properties: {
                x: { type: 'number' },
                y: { type: 'number' },
                w: { type: 'number' },
                h: { type: 'number' },
                id: { type: 'string' }
              },
              required: ['x', 'y', 'w', 'h', 'id'],
              additionalProperties: false
            }
          },
          additionalProperties: false
        }
      },
      required: ['slices'],
      additionalProperties: false
    },
    drawOrder: {
      type: 'array',
      items: { type: 'string' },
      minItems: 1
    },
    anchors: {
      type: 'object',
      patternProperties: {
        '.*': {
          type: 'object',
          properties: {
            x: { type: 'number' },
            y: { type: 'number' }
          },
          required: ['x', 'y'],
          additionalProperties: false
        }
      },
      additionalProperties: false
    }
  },
  required: ['meta', 'images', 'drawOrder', 'anchors'],
  additionalProperties: false
};

// Manifest JSON Schema
export const manifestSchema: JSONSchemaType<Manifest> = {
  type: 'object',
  properties: {
    name: { type: 'string' },
    version: { type: 'string' },
    schema: {
      type: 'object',
      properties: {
        avatar: { type: 'string' },
        bundle: { type: 'string' }
      },
      required: ['avatar', 'bundle'],
      additionalProperties: false
    },
    entry: {
      type: 'object',
      properties: {
        avatar: { type: 'string' },
        graph: { type: 'string', nullable: true }
      },
      required: ['avatar'],
      additionalProperties: false
    },
    rigId: { type: 'string' },
    fitBoxes: {
      type: 'object',
      patternProperties: {
        '.*': {
          type: 'object',
          properties: {
            x: { type: 'number' },
            y: { type: 'number' },
            w: { type: 'number' },
            h: { type: 'number' }
          },
          required: ['x', 'y', 'w', 'h'],
          additionalProperties: false
        }
      },
      additionalProperties: false
    },
    hashes: {
      type: 'object',
      patternProperties: {
        '.*': { type: 'string' }
      },
      additionalProperties: false
    },
    credits: {
      type: 'object',
      nullable: true,
      patternProperties: {
        '.*': {}
      },
      additionalProperties: true
    }
  },
  required: ['name', 'version', 'schema', 'entry', 'rigId', 'fitBoxes', 'hashes'],
  additionalProperties: false
};

// Item JSON Schema
export const itemSchema: JSONSchemaType<Item> = {
  type: 'object',
  properties: {
    type: { type: 'string' },
    sku: { type: 'string' },
    rigId: { type: 'string' },
    fills: {
      type: 'array',
      items: { type: 'string' },
      minItems: 1
    },
    zOffsets: {
      type: 'object',
      patternProperties: {
        '.*': { type: 'number' }
      },
      additionalProperties: false
    },
    fitBox: {
      type: 'object',
      properties: {
        x: { type: 'number' },
        y: { type: 'number' },
        w: { type: 'number' },
        h: { type: 'number' }
      },
      required: ['x', 'y', 'w', 'h'],
      additionalProperties: false
    },
    slices: {
      type: 'object',
      patternProperties: {
        '.*': { type: 'string' }
      },
      additionalProperties: false
    },
    variants: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          name: { type: 'string' },
          tint: { type: 'string' }
        },
        required: ['name', 'tint'],
        additionalProperties: false
      },
      nullable: true
    },
    tags: {
      type: 'array',
      items: { type: 'string' },
      nullable: true
    },
    license: { type: 'string', nullable: true }
  },
  required: ['type', 'sku', 'rigId', 'fills', 'zOffsets', 'fitBox', 'slices'],
  additionalProperties: false
};

export class SchemaValidator {
  private ajv: Ajv;

  constructor() {
    this.ajv = new Ajv({ allErrors: true });
  }

  validateAvatar(avatar: unknown): { valid: boolean; errors: string[] } {
    const validate = this.ajv.compile(avatarSchema);
    const valid = validate(avatar);

    if (!valid) {
      return {
        valid: false,
        errors: validate.errors?.map(error =>
          `${error.instancePath || 'root'}: ${error.message}`
        ) || ['Unknown validation error']
      };
    }

    return { valid: true, errors: [] };
  }

  validateManifest(manifest: unknown): { valid: boolean; errors: string[] } {
    const validate = this.ajv.compile(manifestSchema);
    const valid = validate(manifest);

    if (!valid) {
      return {
        valid: false,
        errors: validate.errors?.map(error =>
          `${error.instancePath || 'root'}: ${error.message}`
        ) || ['Unknown validation error']
      };
    }

    return { valid: true, errors: [] };
  }

  validateItem(item: unknown): { valid: boolean; errors: string[] } {
    const validate = this.ajv.compile(itemSchema);
    const valid = validate(item);

    if (!valid) {
      return {
        valid: false,
        errors: validate.errors?.map(error =>
          `${error.instancePath || 'root'}: ${error.message}`
        ) || ['Unknown validation error']
      };
    }

    return { valid: true, errors: [] };
  }

  validateAvatarCompleteness(avatar: Avatar): { valid: boolean; errors: string[]; warnings: string[] } {
    const errors: string[] = [];
    const warnings: string[] = [];

    // Check for essential slots
    const essentialSlots = [
      'Eyes/EyeL/state/open',
      'Eyes/EyeL/state/closed',
      'Eyes/EyeR/state/open',
      'Eyes/EyeR/state/closed',
      'Mouth/viseme/REST'
    ];

    const missingEssentials = essentialSlots.filter(slot => !avatar.images.slices[slot]);
    if (missingEssentials.length > 0) {
      errors.push(`Missing essential slots: ${missingEssentials.join(', ')}`);
    }

    // Check for recommended visemes
    const recommendedVisemes = [
      'Mouth/viseme/AI',
      'Mouth/viseme/E',
      'Mouth/viseme/U',
      'Mouth/viseme/O',
      'Mouth/viseme/FV'
    ];

    const missingVisemes = recommendedVisemes.filter(slot => !avatar.images.slices[slot]);
    if (missingVisemes.length > 0) {
      warnings.push(`Missing recommended visemes: ${missingVisemes.join(', ')}`);
    }

    // Check for rigId
    if (!avatar.meta.rigId) {
      errors.push('Missing rigId in avatar metadata');
    }

    // Check for essential anchors
    const essentialAnchors = ['headPivot', 'mouthCenter'];
    const missingAnchors = essentialAnchors.filter(anchor => !avatar.anchors[anchor]);
    if (missingAnchors.length > 0) {
      warnings.push(`Missing recommended anchors: ${missingAnchors.join(', ')}`);
    }

    // Check draw order validity
    const slotKeys = Object.keys(avatar.images.slices);
    const unmatchedSlots = slotKeys.filter(slotKey => {
      return !avatar.drawOrder.some(pattern => {
        if (pattern.includes('*')) {
          const prefix = pattern.replace('/*', '');
          return slotKey.startsWith(prefix);
        }
        return slotKey === pattern;
      });
    });

    if (unmatchedSlots.length > 0) {
      warnings.push(`Slots not covered by draw order: ${unmatchedSlots.join(', ')}`);
    }

    return {
      valid: errors.length === 0,
      errors,
      warnings
    };
  }

  validateBundle(
    manifest: unknown,
    avatar: unknown,
    items: unknown[] = []
  ): { valid: boolean; errors: string[]; warnings: string[] } {
    const errors: string[] = [];
    const warnings: string[] = [];

    // Validate manifest
    const manifestResult = this.validateManifest(manifest);
    if (!manifestResult.valid) {
      errors.push(...manifestResult.errors.map(e => `Manifest: ${e}`));
    }

    // Validate avatar
    const avatarResult = this.validateAvatar(avatar);
    if (!avatarResult.valid) {
      errors.push(...avatarResult.errors.map(e => `Avatar: ${e}`));
    } else {
      // Check avatar completeness if basic validation passed
      const completenessResult = this.validateAvatarCompleteness(avatar as Avatar);
      errors.push(...completenessResult.errors);
      warnings.push(...completenessResult.warnings);
    }

    // Validate items
    items.forEach((item, index) => {
      const itemResult = this.validateItem(item);
      if (!itemResult.valid) {
        errors.push(...itemResult.errors.map(e => `Item ${index}: ${e}`));
      }
    });

    // Cross-validate manifest and avatar
    if (manifestResult.valid && avatarResult.valid) {
      const manifestTyped = manifest as Manifest;
      const avatarTyped = avatar as Avatar;

      if (manifestTyped.rigId !== avatarTyped.meta.rigId) {
        warnings.push('Manifest rigId does not match avatar rigId');
      }

      if (manifestTyped.entry.avatar !== 'avatar.json') {
        warnings.push('Manifest entry point should typically be "avatar.json"');
      }
    }

    return {
      valid: errors.length === 0,
      errors,
      warnings
    };
  }
}

export const createSchemaValidator = (): SchemaValidator => {
  return new SchemaValidator();
};