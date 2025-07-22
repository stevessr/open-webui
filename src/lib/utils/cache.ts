// src/lib/utils/cache.ts

import { IDBHelper } from './idb';

const CACHE_EXPIRATION_MS = 5 * 60 * 1000; // 5 minutes

interface CacheEntry<T> {
	timestamp: number;
	data: T;
}

export class DocsCache {
	private static instance: DocsCache;
	private readonly idbHelper: IDBHelper;
	private readonly expirationTime: number;

	private constructor(storeName: string = 'docsCache', expirationTime: number = CACHE_EXPIRATION_MS) {
		this.idbHelper = new IDBHelper(storeName);
		this.expirationTime = expirationTime;
		this.cleanupExpired();
	}

	public static getInstance(): DocsCache {
		if (!DocsCache.instance) {
			DocsCache.instance = new DocsCache();
		}
		return DocsCache.instance;
	}

	public async get<T>(key: string): Promise<T | null> {
		const entry = await this.idbHelper.get<{ timestamp: number; data: T }>(key);

		if (!entry) {
			return null;
		}

		const isExpired = Date.now() - entry.timestamp > this.expirationTime;

		if (isExpired) {
			await this.invalidate(key);
			return null;
		}

		return entry.data;
	}

	public async set<T>(key: string, data: T): Promise<void> {
		const timestamp = Date.now();
		await this.idbHelper.set(key, { data }, timestamp);
	}

	public async invalidate(key: string): Promise<void> {
		await this.idbHelper.invalidate(key);
	}

	public async cleanupExpired(): Promise<void> {
		await this.idbHelper.cleanup(this.expirationTime);
	}

	public async clear(): Promise<void> {
		await this.idbHelper.clear();
	}
}