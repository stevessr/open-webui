<script>
	import { settings, config, selectedFolder } from '$lib/stores';
	import { isVideoUrl } from '$lib/utils';

	export let zIndex = '';
	export let opacity = undefined; // Default opacity
	export let url = undefined;
	$: bgUrl = url !== undefined ? url : $selectedFolder?.meta?.background_image_url || $settings?.backgroundImageUrl || '';
	$: bgOpacity = opacity !== undefined ? opacity : $settings?.backgroundOpacity || 0.25;
</script>

{#if bgUrl}
	{#if isVideoUrl(bgUrl)}
		<video
			src={bgUrl}
			autoplay
			muted
			loop
			class="fixed top-0 left-0 w-full h-full object-cover {zIndex} pointer-events-none"
			style="opacity: {bgOpacity};"
			id="background"
		></video>
	{:else}
		<div
			class="fixed top-0 left-0 w-full h-full bg-cover bg-center bg-no-repeat {zIndex} pointer-events-none"
			style="opacity: {bgOpacity};"
		>
			<img
				src={bgUrl}
				alt=""
				class="w-full h-full object-cover"
				style="opacity: {bgOpacity};"
			/>
		</div>
	{/if}
{/if}
