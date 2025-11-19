<script>
	import { settings, config, selectedFolder } from '$lib/stores';
	import { isVideoUrl } from '$lib/utils';

	export let zIndex = '';
	export let opacity = 0.75; // Default opacity
	$: url = $selectedFolder?.meta?.background_image_url || $settings?.backgroundImageUrl || '';
</script>

{#if url}
	{#if isVideoUrl(url)}
		<video
			src={url}
			autoplay
			muted
			loop
			class="fixed top-0 left-0 w-full h-full object-cover {zIndex} pointer-events-none"
			style="opacity: {opacity};"
			id="background"
		></video>
	{:else}
		<div
			class="fixed top-0 left-0 w-full h-full bg-cover bg-center bg-no-repeat {zIndex} pointer-events-none"
			style="opacity: {opacity};"
		>
			<img
				src={url}
				alt=""
				class="w-full h-full object-cover"
				style="opacity: {opacity};"
			/>	
		</div>
	{/if}
{/if}
