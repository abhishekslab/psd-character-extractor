export class RigId {
  private constructor(private readonly _value: string) {
    if (!_value || _value.trim().length === 0) {
      throw new Error('RigId cannot be empty');
    }
  }

  static create(value: string): RigId {
    return new RigId(value);
  }

  static default(): RigId {
    return new RigId('anime-1024-headA-v1');
  }

  get value(): string {
    return this._value;
  }

  equals(other: RigId): boolean {
    return this._value === other._value;
  }

  toString(): string {
    return this._value;
  }
}