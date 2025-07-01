import { writable } from 'svelte/store';
import type { DocInfo } from '$lib/types';

const createDocsStore = () => {
	const { subscribe, update } = writable<{ docs: DocInfo[]; activeDocId: string | null }>({
		docs: [],
		activeDocId: null
	});

	const openDoc = (doc: DocInfo) => {
		update((state) => {
			const existingDoc = state.docs.find((d) => d.id === doc.id);
			if (existingDoc) {
				return { ...state, activeDocId: doc.id };
			}
			return { ...state, docs: [...state.docs, doc], activeDocId: doc.id };
		});
	};

	const closeDoc = (id: string) => {
		update((state) => {
			const newDocs = state.docs.filter((d) => d.id !== id);
			let newActiveDocId = state.activeDocId;

			if (state.activeDocId === id) {
				if (newDocs.length > 0) {
					const currentIndex = state.docs.findIndex((d) => d.id === id);
					newActiveDocId = newDocs[Math.max(0, currentIndex - 1)].id;
				} else {
					newActiveDocId = null;
				}
			}

			return { docs: newDocs, activeDocId: newActiveDocId };
		});
	};

	const openNewTab = () => {
		update((state) => {
			const { docs, activeDocId } = state;
			const activeDoc = docs.find((d) => d.id === activeDocId);

			if (!activeDoc) {
				return state; // No active doc to copy
			}

			const newDoc: DocInfo = {
				id: crypto.randomUUID(),
				url: activeDoc.url,
				title: `${activeDoc.title}『複製品』`
			};

			return {
				...state,
				docs: [...docs, newDoc],
				activeDocId: newDoc.id
			};
		});
	};

	const selectDoc = (id: string) => {
		update((state) => ({ ...state, activeDocId: id }));
	};

	return {
		subscribe,
		openDoc,
		closeDoc,
		openNewTab,
		selectDoc
	};
};

export const docs = createDocsStore();
