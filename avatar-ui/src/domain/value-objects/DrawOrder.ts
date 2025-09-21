export class DrawOrder {
  private static readonly DEFAULT_PATTERNS = [
    'Body/*',
    'Head/*',
    'Hair/back',
    'Eyes/*',
    'Brows/*',
    'Mouth/*',
    'Nose/*',
    'Cheek/*',
    'Hair/front',
    'Accessories/*',
    'FX/*'
  ];

  private constructor(private readonly _patterns: string[]) {
    if (_patterns.length === 0) {
      throw new Error('DrawOrder must have at least one pattern');
    }
  }

  static create(patterns: string[]): DrawOrder {
    return new DrawOrder([...patterns]);
  }

  static default(): DrawOrder {
    return new DrawOrder([...DrawOrder.DEFAULT_PATTERNS]);
  }

  get patterns(): string[] {
    return [...this._patterns];
  }

  getZIndex(slotPath: string): number {
    for (let i = 0; i < this._patterns.length; i++) {
      const pattern = this._patterns[i];
      if (this.matchesPattern(slotPath, pattern)) {
        return i;
      }
    }
    return this._patterns.length; // Default to end if no match
  }

  private matchesPattern(slotPath: string, pattern: string): boolean {
    if (pattern.includes('*')) {
      const prefix = pattern.replace('/*', '');
      return slotPath.startsWith(prefix);
    }
    return slotPath === pattern;
  }

  addPattern(pattern: string, index?: number): DrawOrder {
    const newPatterns = [...this._patterns];
    if (index !== undefined) {
      newPatterns.splice(index, 0, pattern);
    } else {
      newPatterns.push(pattern);
    }
    return new DrawOrder(newPatterns);
  }

  removePattern(pattern: string): DrawOrder {
    const newPatterns = this._patterns.filter(p => p !== pattern);
    return new DrawOrder(newPatterns);
  }

  sortSlotPaths(slotPaths: string[]): string[] {
    return [...slotPaths].sort((a, b) => this.getZIndex(a) - this.getZIndex(b));
  }

  equals(other: DrawOrder): boolean {
    return this._patterns.length === other._patterns.length &&
           this._patterns.every((pattern, index) => pattern === other._patterns[index]);
  }

  toString(): string {
    return `DrawOrder(${this._patterns.join(', ')})`;
  }
}