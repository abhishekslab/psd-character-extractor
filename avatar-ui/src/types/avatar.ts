export interface SliceInfo {
  x: number;
  y: number;
  w: number;
  h: number;
  id: string;
}

export interface AvatarMeta {
  generator: string;
  rigId: string;
}

export interface Avatar {
  meta: AvatarMeta;
  images: {
    atlas?: string;
    slices: Record<string, SliceInfo>;
  };
  drawOrder: string[];
  anchors: Record<string, { x: number; y: number }>;
}

export interface ManifestFitBox {
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface Manifest {
  name: string;
  version: string;
  schema: {
    avatar: string;
    bundle: string;
  };
  entry: {
    avatar: string;
    graph?: string;
  };
  rigId: string;
  fitBoxes: Record<string, ManifestFitBox>;
  hashes: Record<string, string>;
  credits?: Record<string, any>;
}

export interface PSDPathMapping {
  psdPath: string;
  sliceId: string;
  canonical: string;
}

export interface ItemVariant {
  name: string;
  tint: string;
}

export interface Item {
  type: string;
  sku: string;
  rigId: string;
  fills: string[];
  zOffsets: Record<string, number>;
  fitBox: ManifestFitBox;
  slices: Record<string, string>;
  variants?: ItemVariant[];
  tags?: string[];
  license?: string;
}

export interface ExtractedSlice {
  id: string;
  name: string;
  psdPath: string;
  image: ImageData;
  canvas: HTMLCanvasElement;
  bounds: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  mapped?: boolean;
  canonicalSlot?: string;
}

export interface SlotPalette {
  [partName: string]: {
    [slotName: string]: string[] | Record<string, string[]> | {};
  };
}

export interface AutoMapRule {
  match: string;
  map: {
    group: string;
    slot: string;
  };
}

export interface PCSRules {
  aliases: AutoMapRule[];
}