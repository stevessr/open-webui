<script lang="ts">
	import { getContext } from 'svelte';

	import { generateInitialsImage, isVideoUrl } from '$lib/utils';
	import { convertToProxyUrl, isSameRegistrableDomain } from '$lib/utils/url';

	const i18n = getContext('i18n');

	export let src = '';
	export let name = '';
	export let className = '';
	export let alt = 'profile';
	export let autoplay = true;
	export let muted = true;
	export let loop = true;
	export let style: string = '';
	export let loadingattr: 'eager' | 'lazy' = 'lazy';
	export { className as class }; // 支持 class 作为别名
	export { loadingattr as loading };

	const currentDomain = typeof window !== 'undefined' ? window.location.hostname : '';

	let hasErrorRetried = false;

	$: processedSrc = convertToProxyUrl(src, currentDomain);
	$: if (src) hasErrorRetried = false; // Reset error retry state when src changes
</script>

{#if processedSrc && isVideoUrl(processedSrc)}
	<video
		src={processedSrc}
		class="rounded-full {className} object-cover"
		{autoplay}
		{muted}
		{loop}
		{style}
		loading={loadingattr}
		on:error={(e) => {
			if (currentDomain == '') return; // In non-browser environments, do nothing

			const video = e.target as HTMLVideoElement;

			// 如果已经重试过一次，不再处理错误
			if (hasErrorRetried) return;

			// If error occurs and src is not already a proxy URL, try proxy
			if (src && src !== processedSrc) {
				try {
					const originalUrl = new URL(src);
					if (isSameRegistrableDomain(originalUrl.hostname, currentDomain)) return; // If same domain, do nothing
					video.src = `/op${originalUrl.pathname}${originalUrl.search}${originalUrl.hash}`;
					hasErrorRetried = true;
				} catch (err) {
					// URL parsing failed, do nothing
				}
			} else if (processedSrc !== src) {
				// 如果当前是代理 URL 且失败了，回退到原始 URL
				video.src = src;
				hasErrorRetried = true;
			}
		}}
	></video>
{:else}
	<img
		src={processedSrc !== '' ? processedSrc : generateInitialsImage(name)}
		{alt}
		class="rounded-full {className} object-cover"
		{style}
		loading={loadingattr}
		on:error={(e) => {
			if (currentDomain == '') return; // In non-browser environments, do nothing

			const img = e.target as HTMLImageElement;

			// 如果已经重试过一次，不再处理错误
			if (hasErrorRetried) return;

			// If error occurs and src is not already a proxy URL, try proxy
			if (src && src !== processedSrc) {
				try {
					const originalUrl = new URL(src);
					if (isSameRegistrableDomain(originalUrl.hostname, currentDomain)) return; // If same domain, do nothing
					img.src = `/op${originalUrl.pathname}${originalUrl.search}${originalUrl.hash}`;
					hasErrorRetried = true;
				} catch (err) {
					// URL parsing failed, do nothing
				}
			} else if (processedSrc !== src && processedSrc !== generateInitialsImage(name)) {
				// 如果当前是代理 URL 且失败了，回退到原始 URL
				img.src = src;
				hasErrorRetried = true;
			} else if (processedSrc === generateInitialsImage(name)) {
				// 如果是初始头像图片失败，什么都不做
				hasErrorRetried = true;
			}
		}}
	/>
{/if}
