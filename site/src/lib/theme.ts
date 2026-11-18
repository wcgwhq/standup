import css from '@/styles/global.css?raw';

/** Every value of a --color-<name> token in global.css: the light one first, then the dark one. */
export const colors = (name: string) =>
  [...css.matchAll(new RegExp(`--color-${name}:\\s*([^;]+);`, 'g'))].map(([, value]) => value.trim());
