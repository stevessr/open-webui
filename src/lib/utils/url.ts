/**
 * 提取主机名的可注册域名部分。
 * 例如 'www.google.com' -> 'google.com'
 * 'a.b.c' -> 'b.c'
 */
export function getRegistrableDomain(hostname: string): string {
	if (!hostname) return '';
	const parts = hostname.split('.');
	if (parts.length > 2) {
		return parts.slice(-2).join('.');
	}
	return hostname;
}

/**
 * 检查两个主机名是否属于同一个可注册域名。
 * 例如 isSameRegistrableDomain('a.example.com', 'b.example.com') => true
 * isSameRegistrableDomain('a.example.com', 'a.another.com') => false
 */
export function isSameRegistrableDomain(hostname1: string, hostname2: string): boolean {
	const domain1 = getRegistrableDomain(hostname1);
	const domain2 = getRegistrableDomain(hostname2);
	return domain1 === domain2 && domain1 !== '';
}

/**
 * 将跨域 URL 转换为代理 URL
 * @param url 原始 URL
 * @param currentDomain 当前域名
 * @returns 转换后的 URL 或原始 URL
 */
export function convertToProxyUrl(url: string, currentDomain: string): string {
	try {
		if (!url) return url;
		if (currentDomain == '') return url; // In non-browser environments, return original URL

		// 如果已经是代理路径，直接返回
		if (url.startsWith('/op/')) return url;

		// 跳过 base64 编码的 URL (data: scheme)
		if (url.startsWith('data:')) return url;

		// 跳过非 HTTP(S) 协议的 URL
		if (!url.startsWith('http://') && !url.startsWith('https://')) return url;

		const urlObj = new URL(url);

		// 检查是否为外部图片存储服务，如果是则不进行代理处理
		const externalImageServices = [
			'bed.stevessr.eu.org',
			'cdn.jsdelivr.net',
			'githubusercontent.com',
			'discord.com',
			'discordapp.com',
			'media.discordapp.net',
			'images.unsplash.com',
			'pixabay.com',
			'pexels.com',
			'storyblok.com',
			'cloudinary.com',
			'imgur.com',
			'i.imgur.com',
			'ibb.co'
		];

		// 如果是外部图片服务，直接返回原始 URL
		if (externalImageServices.some(service => urlObj.hostname.includes(service))) {
			return url;
		}

		// 如果两个 URL 不属于同一个主域名，则转换为代理 URL
		if (!isSameRegistrableDomain(urlObj.hostname, currentDomain)) {
			return `/op${urlObj.pathname}${urlObj.search}${urlObj.hash}`;
		}
		return url;
	} catch (e) {
		return url; // Return original URL if parsing fails
	}
}