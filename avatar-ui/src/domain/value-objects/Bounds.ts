export class Bounds {
  constructor(
    private readonly _x: number,
    private readonly _y: number,
    private readonly _width: number,
    private readonly _height: number
  ) {
    if (_width < 0 || _height < 0) {
      throw new Error('Bounds dimensions must be non-negative');
    }
  }

  static create(x: number, y: number, width: number, height: number): Bounds {
    return new Bounds(x, y, width, height);
  }

  get x(): number {
    return this._x;
  }

  get y(): number {
    return this._y;
  }

  get width(): number {
    return this._width;
  }

  get height(): number {
    return this._height;
  }

  get area(): number {
    return this._width * this._height;
  }

  get right(): number {
    return this._x + this._width;
  }

  get bottom(): number {
    return this._y + this._height;
  }

  get center(): { x: number; y: number } {
    return {
      x: this._x + this._width / 2,
      y: this._y + this._height / 2
    };
  }

  contains(point: { x: number; y: number }): boolean {
    return point.x >= this._x &&
           point.x <= this.right &&
           point.y >= this._y &&
           point.y <= this.bottom;
  }

  intersects(other: Bounds): boolean {
    return !(this.right < other._x ||
             this._x > other.right ||
             this.bottom < other._y ||
             this._y > other.bottom);
  }

  union(other: Bounds): Bounds {
    const minX = Math.min(this._x, other._x);
    const minY = Math.min(this._y, other._y);
    const maxX = Math.max(this.right, other.right);
    const maxY = Math.max(this.bottom, other.bottom);

    return new Bounds(minX, minY, maxX - minX, maxY - minY);
  }

  equals(other: Bounds): boolean {
    return this._x === other._x &&
           this._y === other._y &&
           this._width === other._width &&
           this._height === other._height;
  }

  toString(): string {
    return `Bounds(${this._x}, ${this._y}, ${this._width}, ${this._height})`;
  }
}