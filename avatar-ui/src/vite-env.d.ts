/// <reference types="vite/client" />

declare module "*.json" {
  const value: any;
  export default value;
}

declare module "psd.js" {
  interface PSDOptions {
    [key: string]: any;
  }

  class PSD {
    static fromDroppedFile(file: File): PSD;
    static fromURL(url: string): PSD;
    static fromArrayBuffer(buffer: ArrayBuffer): PSD;

    parse(): Promise<void>;
    image: {
      toPng(): Uint8Array;
    };
    tree: {
      children: any[];
    };
    header: {
      width: number;
      height: number;
    };
  }

  export = PSD;
}
