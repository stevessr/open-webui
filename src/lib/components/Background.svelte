<script>
	import { settings, config, selectedFolder } from '$lib/stores';
	import { isVideoUrl } from '$lib/utils';

	export let zIndex = '-z-10';
	export let opacity = 0.3; // Default opacity
	export let url =
		$selectedFolder?.meta?.background_image_url ||
		$settings?.backgroundImageUrl ||
		'' ;
	if(selectedFolder){
		console.log("selected",selectedFolder)
	}
	console.log("url in Background.svelte:", url);
</script>

{#if url}
	{#if isVideoUrl(url)}
		<video
			src={url}
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
			style="opacity: {opacity};"
		><img src={url} alt="Background Image" class="w-full h-full object-cover" style="opacity: {opacity};"/></div>
	{/if}
{/if}
