<script lang="ts">
	import { WEBUI_BASE_URL } from '$lib/constants';
	import { onMount } from 'svelte';
	import { isVideoUrl } from '$lib/utils';

	export let imageUrls = [
		`${WEBUI_BASE_URL}/assets/images/adam.jpg`,
		`${WEBUI_BASE_URL}/assets/images/galaxy.jpg`,
		`${WEBUI_BASE_URL}/assets/images/earth.jpg`,
		`${WEBUI_BASE_URL}/assets/images/space.jpg`
	];
	export let duration = 5000;
	let selectedImageIdx = 0;

	onMount(() => {
		setInterval(() => {
			selectedImageIdx = (selectedImageIdx + 1) % (imageUrls.length - 1);
		}, duration);
	});
</script>

{#each imageUrls as imageUrl, idx (idx)}
	<div
		class="image w-full h-full absolute top-0 left-0 transition-opacity duration-1000"
		style="opacity: {selectedImageIdx === idx ? 1 : 0};"
	>
		{#if isVideoUrl(imageUrl)}
			<video src={imageUrl} autoplay muted loop class="w-full h-full object-cover" />
		{:else}
			<div class="w-full h-full bg-cover bg-center" style="background-image: url('{imageUrl}')" />
		{/if}
	</div>
{/each}

<style>
	.image {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		background-size: cover;
		background-position: center; /* Center the background images */
		transition: opacity 1s ease-in-out; /* Smooth fade effect */
		opacity: 0; /* Make images initially not visible */
	}
</style>
