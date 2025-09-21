import { SliceMapping } from './SliceMapping';
import { AnchorPoint } from '../value-objects/AnchorPoint';
import { DrawOrder } from '../value-objects/DrawOrder';
import { RigId } from '../value-objects/RigId';

export class Avatar {
  constructor(
    private _id: string,
    private _rigId: RigId,
    private _sliceMappings: Map<string, SliceMapping>,
    private _drawOrder: DrawOrder,
    private _anchors: Map<string, AnchorPoint>,
    private _generator: string = 'psd-ce@1.0.0'
  ) {}

  get id(): string {
    return this._id;
  }

  get rigId(): RigId {
    return this._rigId;
  }

  get sliceMappings(): Map<string, SliceMapping> {
    return new Map(this._sliceMappings);
  }

  get drawOrder(): DrawOrder {
    return this._drawOrder;
  }

  get anchors(): Map<string, AnchorPoint> {
    return new Map(this._anchors);
  }

  get generator(): string {
    return this._generator;
  }

  addSliceMapping(slotPath: string, mapping: SliceMapping): void {
    this._sliceMappings.set(slotPath, mapping);
  }

  removeSliceMapping(slotPath: string): void {
    this._sliceMappings.delete(slotPath);
  }

  getSliceMapping(slotPath: string): SliceMapping | undefined {
    return this._sliceMappings.get(slotPath);
  }

  hasSliceMapping(slotPath: string): boolean {
    return this._sliceMappings.has(slotPath);
  }

  addAnchor(name: string, point: AnchorPoint): void {
    this._anchors.set(name, point);
  }

  getAnchor(name: string): AnchorPoint | undefined {
    return this._anchors.get(name);
  }

  getSlotPaths(): string[] {
    return Array.from(this._sliceMappings.keys());
  }

  clone(): Avatar {
    return new Avatar(
      this._id,
      this._rigId,
      new Map(this._sliceMappings),
      this._drawOrder,
      new Map(this._anchors),
      this._generator
    );
  }

  toJSON() {
    return {
      meta: {
        generator: this._generator,
        rigId: this._rigId.value
      },
      images: {
        slices: Object.fromEntries(
          Array.from(this._sliceMappings.entries()).map(([slot, mapping]) => [
            slot,
            {
              x: mapping.bounds.x,
              y: mapping.bounds.y,
              w: mapping.bounds.width,
              h: mapping.bounds.height,
              id: mapping.sliceId
            }
          ])
        )
      },
      drawOrder: this._drawOrder.patterns,
      anchors: Object.fromEntries(
        Array.from(this._anchors.entries()).map(([name, point]) => [
          name,
          { x: point.x, y: point.y }
        ])
      )
    };
  }
}