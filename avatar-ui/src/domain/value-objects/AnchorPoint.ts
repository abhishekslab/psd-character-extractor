export class AnchorPoint {
  constructor(
    private readonly _x: number,
    private readonly _y: number
  ) {}

  static create(x: number, y: number): AnchorPoint {
    return new AnchorPoint(x, y);
  }

  get x(): number {
    return this._x;
  }

  get y(): number {
    return this._y;
  }

  distanceTo(other: AnchorPoint): number {
    const dx = this._x - other._x;
    const dy = this._y - other._y;
    return Math.sqrt(dx * dx + dy * dy);
  }

  translate(dx: number, dy: number): AnchorPoint {
    return new AnchorPoint(this._x + dx, this._y + dy);
  }

  equals(other: AnchorPoint): boolean {
    return this._x === other._x && this._y === other._y;
  }

  toString(): string {
    return `AnchorPoint(${this._x}, ${this._y})`;
  }
}