export class Color {
  private constructor(private readonly _value: string) {
    if (!this.isValidHex(_value)) {
      throw new Error('Color must be a valid hex color (e.g., #ffffff)');
    }
  }

  static create(value: string): Color {
    return new Color(value);
  }

  static white(): Color {
    return new Color('#ffffff');
  }

  static black(): Color {
    return new Color('#000000');
  }

  static fromRgb(r: number, g: number, b: number): Color {
    const hex = '#' + [r, g, b]
      .map(x => Math.round(Math.max(0, Math.min(255, x))).toString(16).padStart(2, '0'))
      .join('');
    return new Color(hex);
  }

  get value(): string {
    return this._value;
  }

  get rgb(): { r: number; g: number; b: number } {
    const hex = this._value.substring(1);
    return {
      r: parseInt(hex.substring(0, 2), 16),
      g: parseInt(hex.substring(2, 4), 16),
      b: parseInt(hex.substring(4, 6), 16)
    };
  }

  get brightness(): number {
    const { r, g, b } = this.rgb;
    return (r * 299 + g * 587 + b * 114) / 1000;
  }

  get isLight(): boolean {
    return this.brightness > 128;
  }

  get isDark(): boolean {
    return !this.isLight;
  }

  withAlpha(alpha: number): string {
    const clampedAlpha = Math.max(0, Math.min(1, alpha));
    const { r, g, b } = this.rgb;
    return `rgba(${r}, ${g}, ${b}, ${clampedAlpha})`;
  }

  private isValidHex(value: string): boolean {
    return /^#[0-9A-F]{6}$/i.test(value);
  }

  equals(other: Color): boolean {
    return this._value.toLowerCase() === other._value.toLowerCase();
  }

  toString(): string {
    return this._value;
  }
}