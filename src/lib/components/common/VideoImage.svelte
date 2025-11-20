<script lang="ts">
	import { isVideoUrl } from '$lib/utils/index';
	import ProfileImage from './ProfileImage.svelte';

	export let src: string = '';
	export let alt: string = '';
	export let className: string = '';
	export let crossOrigin: 'use-credentials' | 'anonymous' | '' | undefined = 'anonymous';
	export let controls: boolean = true;
	export let autoplay: boolean = false;
	export let muted: boolean = false;
	export let loop: boolean = false;
	export let opacity: number | null = null;

	const currentDomain = typeof window !== 'undefined' ? window.location.hostname : '';
	const origin = typeof window !== 'undefined' ? window.location.origin : '';

	/**
	 * 提取主机名的可注册域名部分。
	 * 例如 'www.google.com' -> 'google.com'
	 * 'a.b.c' -> 'b.c'
	 */
	function getRegistrableDomain(hostname: string): string {
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
	function isSameRegistrableDomain(hostname1: string, hostname2: string): boolean {
		const domain1 = getRegistrableDomain(hostname1);
		const domain2 = getRegistrableDomain(hostname2);
		return domain1 === domain2 && domain1 !== '';
	}

	// Function to convert cross-domain URLs to proxy URLs
	const convertToProxyUrl = (url: string): string => {
		try {
			if (!url) return url;
			if (currentDomain == '') return url; // In non-browser environments, return original URL

			const urlObj = new URL(url);
			// 如果两个 URL 不属于同一个主域名，则转换为代理 URL
			if (!isSameRegistrableDomain(urlObj.hostname, currentDomain)) {
				return `/op${urlObj.pathname}${urlObj.search}${urlObj.hash}`;
			}
			return url;
		} catch (e) {
			return url; // Return original URL if parsing fails
		}
	};

	$: processedSrc = convertToProxyUrl(src);
	$: isVideo = processedSrc && isVideoUrl(processedSrc);
</script>

{#if isVideo}
	<video
		src={processedSrc}
		{controls}
		{autoplay}
		{muted}
		{loop}
		class={className}
		crossorigin={crossOrigin}
		data-cy="video"
		title={alt}
		on:error={(e) => {
			if (currentDomain == '') return; // In non-browser environments, do nothing

			const video = e.target as HTMLVideoElement;
			// If error occurs and src is not already a proxy URL, try proxy
			if (src && src !== processedSrc) {
				const originalUrl = new URL(src);
				if (isSameRegistrableDomain(originalUrl.hostname, currentDomain)) return; // If same domain, do nothing
				video.src = `${origin}/op${originalUrl.pathname}${originalUrl.search}${originalUrl.hash}`;
			}
		}}
	>
		Your browser does not support the video tag.
	</video>
{:else}
	<ProfileImage src={processedSrc} {alt} {className} style="opacity: {opacity}" />
{/if}
