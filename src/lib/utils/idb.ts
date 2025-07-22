// src/lib/utils/idb.ts

const DB_NAME = 'open-webui-db';
const DB_VERSION = 1;

export class IDBHelper {
	private db: Promise<IDBDatabase>;

	constructor(private storeName: string) {
		this.db = new Promise((resolve, reject) => {
			const request = indexedDB.open(DB_NAME, DB_VERSION);

			request.onerror = () => reject(request.error);
			request.onsuccess = () => resolve(request.result);

			request.onupgradeneeded = (event) => {
				const db = (event.target as IDBOpenDBRequest).result;
				if (!db.objectStoreNames.contains(this.storeName)) {
					db.createObjectStore(this.storeName, { keyPath: 'key' });
				}
			};
		});
	}

	private async getStore(mode: IDBTransactionMode): Promise<IDBObjectStore> {
		const db = await this.db;
		return db.transaction(this.storeName, mode).objectStore(this.storeName);
	}

	public async get<T>(key: string): Promise<T | null> {
		const store = await this.getStore('readonly');
		const request = store.get(key);

		return new Promise((resolve, reject) => {
			request.onerror = () => reject(request.error);
			request.onsuccess = () => resolve(request.result?.data ?? null);
		});
	}

	public async set<T>(key: string, data: T, timestamp: number): Promise<void> {
		const store = await this.getStore('readwrite');
		const request = store.put({ key, data, timestamp });

		return new Promise((resolve, reject) => {
			request.onerror = () => reject(request.error);
			request.onsuccess = () => resolve();
		});
	}

	public async invalidate(key: string): Promise<void> {
		const store = await this.getStore('readwrite');
		const request = store.delete(key);

		return new Promise((resolve, reject) => {
			request.onerror = () => reject(request.error);
			request.onsuccess = () => resolve();
		});
	}

	public async cleanup(expirationTime: number): Promise<void> {
		const store = await this.getStore('readwrite');
		const request = store.openCursor();

		request.onsuccess = (event) => {
			const cursor = (event.target as IDBRequest<IDBCursorWithValue>).result;
			if (cursor) {
				const isExpired = Date.now() - cursor.value.timestamp > expirationTime;
				if (isExpired) {
					cursor.delete();
				}
				cursor.continue();
			}
		};

		return new Promise((resolve, reject) => {
			request.onerror = () => reject(request.error);
			// This will resolve when the cursor is done
			store.transaction.oncomplete = () => resolve();
		});
	}

	public async clear(): Promise<void> {
		const store = await this.getStore('readwrite');
		const request = store.clear();

		return new Promise((resolve, reject) => {
			request.onerror = () => reject(request.error);
			request.onsuccess = () => resolve();
		});
	}
}