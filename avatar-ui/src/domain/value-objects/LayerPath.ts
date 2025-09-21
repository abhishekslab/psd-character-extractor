export class LayerPath {
  private constructor(private readonly _value: string) {
    if (!_value || _value.trim().length === 0) {
      throw new Error('LayerPath cannot be empty');
    }
  }

  static create(value: string): LayerPath {
    return new LayerPath(value);
  }

  static fromSegments(segments: string[]): LayerPath {
    if (segments.length === 0) {
      throw new Error('LayerPath must have at least one segment');
    }
    return new LayerPath(segments.join('/'));
  }

  get value(): string {
    return this._value;
  }

  get segments(): string[] {
    return this._value.split('/');
  }

  get leafName(): string {
    const segments = this.segments;
    return segments[segments.length - 1];
  }

  get parentPath(): LayerPath | null {
    const segments = this.segments;
    if (segments.length <= 1) {
      return null;
    }
    return LayerPath.create(segments.slice(0, -1).join('/'));
  }

  startsWith(prefix: string): boolean {
    return this._value.startsWith(prefix);
  }

  contains(segment: string): boolean {
    return this.segments.includes(segment);
  }

  equals(other: LayerPath): boolean {
    return this._value === other._value;
  }

  toString(): string {
    return this._value;
  }
}