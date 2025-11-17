interface CacheEntry<T> {
	data: T;
	timestamp: number;
}

class APICache {
	private cache = new Map<string, CacheEntry<any>>();
	private defaultTTL = 5 * 60 * 1000; // 5 分钟默认缓存时间

	set<T>(key: string, data: T, ttl: number = this.defaultTTL): void {
		this.cache.set(key, {
			data,
			timestamp: Date.now() + ttl
		});
	}

	get<T>(key: string): T | null {
		const entry = this.cache.get(key);
		if (!entry) {
			return null;
		}

		if (Date.now() > entry.timestamp) {
			this.cache.delete(key);
			return null;
		}

		return entry.data;
	}

	clear(): void {
		this.cache.clear();
	}

	delete(key: string): void {
		this.cache.delete(key);
	}

	// 清理过期缓存
	cleanup(): void {
		const now = Date.now();
		for (const [key, entry] of this.cache.entries()) {
			if (now > entry.timestamp) {
				this.cache.delete(key);
			}
		}
	}
}

// 创建全局缓存实例
const apiCache = new APICache();

// 定期清理过期缓存
setInterval(() => {
	apiCache.cleanup();
}, 60000); // 每分钟清理一次

export default apiCache;
