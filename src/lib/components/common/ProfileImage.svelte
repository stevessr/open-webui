<script lang="ts">
	import { getContext } from 'svelte';

	import { generateInitialsImage, isVideoUrl } from '$lib/utils';

	const i18n = getContext('i18n');

	export let src = '';
	export let name = '';
	export let className = '';
	export let alt = 'profile';
	export let autoplay = true;
	export let muted = true;
	export let loop = true;

	const currentDomain = typeof window !== 'undefined' ? window.location.hostname : '';

	// Function to convert cross-domain URLs to proxy URLs
	const convertToProxyUrl = (url: string): string => {
		try {
			if (!url) return url;

			const urlObj = new URL(url);
			// If the domain is different from current domain, convert to proxy URL
			if (urlObj.hostname !== currentDomain) {
				return `/op${urlObj.pathname}${urlObj.search}${urlObj.hash}`;
			}
			return url;
		} catch (e) {
			return url; // Return original URL if parsing fails
		}
	};

	$: processedSrc = convertToProxyUrl(src);
</script>

{#if processedSrc && isVideoUrl(processedSrc)}
	<video src={processedSrc} {alt} class="rounded-full {className} object-cover" {autoplay} {muted} {loop}
		on:error={(e) => {
			const video = e.target as HTMLVideoElement;
			// If error occurs and src is not already a proxy URL, try proxy
			if (src && src !== processedSrc) {
				const originalUrl = new URL(src);
				if (originalUrl.hostname !== currentDomain) {
					video.src = `/op${originalUrl.pathname}${originalUrl.search}${originalUrl.hash}`;
				}
			}
		}}
	></video>
{:else}
	<img
		src={processedSrc !== '' ? processedSrc : generateInitialsImage(name)}
		{alt}
		class="rounded-full {className} object-cover"
		loading="lazy"
		on:error={(e) => {
			const img = e.target as HTMLImageElement;
			// If error occurs and src is not already a proxy URL, try proxy
			if (src && src !== processedSrc) {
				const originalUrl = new URL(src);
				if (originalUrl.hostname !== currentDomain) {
					img.src = `/op${originalUrl.pathname}${originalUrl.search}${originalUrl.hash}`;
				}
			}
		}}
	/>
{/if}
