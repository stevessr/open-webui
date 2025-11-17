<script>
	import { settings, config } from '$lib/stores';
	import { isVideoUrl } from '$lib/utils';

	export let zIndex = '-z-10';
	export let opacity = 0.3; // Default opacity
</script>

{#if $settings?.backgroundImageUrl}
	{#if isVideoUrl($settings?.backgroundImageUrl)}
		<video
			src={$settings?.backgroundImageUrl}
			autoplay
			muted
			loop
			class="fixed top-0 left-0 w-full h-full object-cover {zIndex}"
			style="opacity: {opacity};"
			id="background"
		></video>
	{:else}
		<div
			class="fixed top-0 left-0 w-full h-full bg-cover bg-center bg-no-repeat {zIndex}"
			style="background-image: url({$settings?.backgroundImageUrl ?? null}); opacity: {opacity};"
		></div>
	{/if}
{/if}
