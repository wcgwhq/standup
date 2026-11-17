/// <reference types="astro/client" />

interface Window {
  /** Microsoft Clarity's queue function; absent where Clarity is not loaded. */
  clarity?: (...args: unknown[]) => void;
}
