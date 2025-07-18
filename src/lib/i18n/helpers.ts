import { getContext } from 'svelte';
import type { Readable } from 'svelte/store';

export interface I18nStore extends Readable<any> {
  t: (key: string, options?: Record<string, any>) => string;
  changeLanguage: (lang: string) => void;
}

/**
 * Helper function to get the i18n store from context
 * Use this in components that need to access i18n
 */
export function getI18n(): I18nStore {
  return getContext<I18nStore>('i18n');
}
