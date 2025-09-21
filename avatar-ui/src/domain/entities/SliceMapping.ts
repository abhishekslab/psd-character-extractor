import { SliceId } from '../value-objects/SliceId';
import { Bounds } from '../value-objects/Bounds';
import { ZOffset } from '../value-objects/ZOffset';
import { Color } from '../value-objects/Color';

export class SliceMapping {
  constructor(
    private _sliceId: SliceId,
    private _bounds: Bounds,
    private _zOffset: ZOffset = ZOffset.default(),
    private _tint: Color = Color.white(),
    private _isVisible: boolean = true
  ) {}

  get sliceId(): SliceId {
    return this._sliceId;
  }

  get bounds(): Bounds {
    return this._bounds;
  }

  get zOffset(): ZOffset {
    return this._zOffset;
  }

  get tint(): Color {
    return this._tint;
  }

  get isVisible(): boolean {
    return this._isVisible;
  }

  setZOffset(offset: ZOffset): SliceMapping {
    return new SliceMapping(
      this._sliceId,
      this._bounds,
      offset,
      this._tint,
      this._isVisible
    );
  }

  setTint(color: Color): SliceMapping {
    return new SliceMapping(
      this._sliceId,
      this._bounds,
      this._zOffset,
      color,
      this._isVisible
    );
  }

  setVisibility(visible: boolean): SliceMapping {
    return new SliceMapping(
      this._sliceId,
      this._bounds,
      this._zOffset,
      this._tint,
      visible
    );
  }

  clone(): SliceMapping {
    return new SliceMapping(
      this._sliceId,
      this._bounds,
      this._zOffset,
      this._tint,
      this._isVisible
    );
  }

  equals(other: SliceMapping): boolean {
    return this._sliceId.equals(other._sliceId);
  }
}