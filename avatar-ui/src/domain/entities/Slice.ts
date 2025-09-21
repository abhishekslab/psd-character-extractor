import { SliceId } from '../value-objects/SliceId';
import { Bounds } from '../value-objects/Bounds';
import { LayerPath } from '../value-objects/LayerPath';

export class Slice {
  constructor(
    private _id: SliceId,
    private _name: string,
    private _layerPath: LayerPath,
    private _bounds: Bounds,
    private _canvas: HTMLCanvasElement,
    private _imageData: ImageData,
    private _isVisible: boolean = true
  ) {}

  get id(): SliceId {
    return this._id;
  }

  get name(): string {
    return this._name;
  }

  get layerPath(): LayerPath {
    return this._layerPath;
  }

  get bounds(): Bounds {
    return this._bounds;
  }

  get canvas(): HTMLCanvasElement {
    return this._canvas;
  }

  get imageData(): ImageData {
    return this._imageData;
  }

  get isVisible(): boolean {
    return this._isVisible;
  }

  setVisibility(visible: boolean): void {
    this._isVisible = visible;
  }

  getArea(): number {
    return this._bounds.width * this._bounds.height;
  }

  toDataURL(): string {
    return this._canvas.toDataURL('image/png');
  }

  clone(): Slice {
    // Clone the canvas
    const clonedCanvas = document.createElement('canvas');
    clonedCanvas.width = this._canvas.width;
    clonedCanvas.height = this._canvas.height;
    const ctx = clonedCanvas.getContext('2d');
    if (ctx) {
      ctx.drawImage(this._canvas, 0, 0);
    }

    // Clone image data
    const clonedImageData = new ImageData(
      new Uint8ClampedArray(this._imageData.data),
      this._imageData.width,
      this._imageData.height
    );

    return new Slice(
      this._id,
      this._name,
      this._layerPath,
      this._bounds,
      clonedCanvas,
      clonedImageData,
      this._isVisible
    );
  }

  equals(other: Slice): boolean {
    return this._id.equals(other._id);
  }
}