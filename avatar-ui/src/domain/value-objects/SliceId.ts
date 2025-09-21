export class SliceId {
  private constructor(private readonly _value: string) {
    if (!_value || _value.trim().length === 0) {
      throw new Error('SliceId cannot be empty');
    }
  }

  static create(value: string): SliceId {
    return new SliceId(value);
  }

  static generate(index: number): SliceId {
    return new SliceId(`slice_${index.toString().padStart(3, '0')}`);
  }

  get value(): string {
    return this._value;
  }

  equals(other: SliceId): boolean {
    return this._value === other._value;
  }

  toString(): string {
    return this._value;
  }
}