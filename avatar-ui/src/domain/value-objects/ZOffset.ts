export class ZOffset {
  private static readonly MIN_VALUE = -2;
  private static readonly MAX_VALUE = 2;

  private constructor(private readonly _value: number) {
    if (_value < ZOffset.MIN_VALUE || _value > ZOffset.MAX_VALUE) {
      throw new Error(`ZOffset must be between ${ZOffset.MIN_VALUE} and ${ZOffset.MAX_VALUE}`);
    }
  }

  static create(value: number): ZOffset {
    return new ZOffset(value);
  }

  static default(): ZOffset {
    return new ZOffset(0);
  }

  static min(): ZOffset {
    return new ZOffset(ZOffset.MIN_VALUE);
  }

  static max(): ZOffset {
    return new ZOffset(ZOffset.MAX_VALUE);
  }

  get value(): number {
    return this._value;
  }

  increment(): ZOffset {
    const newValue = Math.min(this._value + 1, ZOffset.MAX_VALUE);
    return new ZOffset(newValue);
  }

  decrement(): ZOffset {
    const newValue = Math.max(this._value - 1, ZOffset.MIN_VALUE);
    return new ZOffset(newValue);
  }

  canIncrement(): boolean {
    return this._value < ZOffset.MAX_VALUE;
  }

  canDecrement(): boolean {
    return this._value > ZOffset.MIN_VALUE;
  }

  equals(other: ZOffset): boolean {
    return this._value === other._value;
  }

  toString(): string {
    return this._value.toString();
  }
}