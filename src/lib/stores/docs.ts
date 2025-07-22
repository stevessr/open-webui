import { writable } from 'svelte/store';
import type { DocInfo } from '$lib/types';
import { DocsCache } from '$lib/utils/cache';

const createDocsStore = () => {
	const { subscribe, set, update } = writable<DocInfo | null>(null);
	const cache = DocsCache.getInstance();

	const fetchDocContent = async (url: string) => {
		const cachedContent = await cache.get<string>(url);
		if (cachedContent) {
			update((state) => (state ? { ...state, content: cachedContent, isLoading: false } : null));
			return;
		}

		try {
			const response = await fetch(url);
			if (!response.ok) {
				throw new Error(`Failed to fetch doc from ${url}`);
			}
			const content = await response.text();
			await cache.set(url, content);
			update((state) => (state ? { ...state, content, isLoading: false } : null));
		} catch (error) {
			console.error(error);
			update((state) => (state ? { ...state, isLoading: false } : state));
		}
	};

	const openDoc = (doc: DocInfo) => {
		set({ ...doc, isLoading: true });
		if (doc.url) {
			fetchDocContent(doc.url);
		}
	};

	const closeDoc = () => {
		set(null);
	};

	const updateDoc = (updatedFields: Partial<Omit<DocInfo, 'id'>>) => {
		update((state) => {
			if (!state) return null;

			const newDoc = { ...state, ...updatedFields };
			if (updatedFields.url && updatedFields.url !== state.url) {
				newDoc.isLoading = true;
				fetchDocContent(updatedFields.url);
			}
			return newDoc;
		});
	};

	return {
		subscribe,
		openDoc,
		closeDoc,
		updateDoc,
		fetchDocContent
	};
};

export const docs = createDocsStore();
