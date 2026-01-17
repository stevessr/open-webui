<script lang="ts">
	import { isVideoUrl } from '$lib/utils/index';
	import { convertToProxyUrl, isSameRegistrableDomain } from '$lib/utils/url';
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

	let hasErrorRetried = false;

	$: processedSrc = convertToProxyUrl(src, currentDomain);
	$: isVideo = processedSrc && isVideoUrl(processedSrc);
	$: if (src) hasErrorRetried = false; // Reset error retry state when src changes
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

			// 如果已经重试过一次，不再处理错误
			if (hasErrorRetried) return;

			// If error occurs and src is not already a proxy URL, try proxy
			if (src && src !== processedSrc) {
				const originalUrl = new URL(src);
				if (isSameRegistrableDomain(originalUrl.hostname, currentDomain)) return; // If same domain, do nothing
				video.src = `${origin}/op${originalUrl.pathname}${originalUrl.search}${originalUrl.hash}`;
				hasErrorRetried = true;
			} else if (processedSrc !== src) {
				// 如果当前是代理 URL 且失败了，回退到原始 URL
				video.src = src;
				hasErrorRetried = true;
			}
		}}
	>
		Your browser does not support the video tag.
	</video>
{:else}
	<ProfileImage src={processedSrc} {alt} class={className} style="opacity: {opacity}" />
{/if}