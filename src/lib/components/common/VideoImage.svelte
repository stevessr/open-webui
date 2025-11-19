<script lang="ts">
	import { isVideoUrl } from '$lib/utils/index';
	import ProfileImage from './ProfileImage.svelte';

	export let src: string = '';
	export let alt: string = '';
	export let className: string = '';
	export let crossOrigin: string | null = null;
	export let controls: boolean = true;
	export let autoplay: boolean = false;
	export let muted: boolean = false;
	export let loop: boolean = false;
	export let opacity: number | null = null;

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
			const video = e.target as HTMLVideoElement;
			// If error occurs and src is not already a proxy URL, try proxy
			if (src && src !== processedSrc) {
				const originalUrl = new URL(src);
				if (originalUrl.hostname !== currentDomain) {
					video.src = `/op${originalUrl.pathname}${originalUrl.search}${originalUrl.hash}`;
				}
			}
		}}
	>
		Your browser does not support the video tag.
	</video>
{:else}
	<ProfileImage src={processedSrc} {alt} {className} style="opacity: {opacity}" />
{/if}
