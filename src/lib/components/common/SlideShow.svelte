<script lang="ts">

	export let imageUrls = [
		`${WEBUI_BASE_URL}/assets/images/adam.jpg`,
		`${WEBUI_BASE_URL}/assets/images/galaxy.jpg`,
		`${WEBUI_BASE_URL}/assets/images/earth.jpg`,
		`${WEBUI_BASE_URL}/assets/images/space.jpg`
	];
	export let duration = 5000;
	export let preloadImages = true;

	let selectedImageIdx = 0;
	let imagesLoaded = new Set<number>();

	// Preload images for better performance
	const preloadImage = (url: string, index: number) => {
		const img = new Image();
		img.onload = () => {
			imagesLoaded.add(index);
			imagesLoaded = imagesLoaded; // Trigger reactivity
		};
		img.src = url;
	};

	onMount(() => {
		// Preload all images if enabled
		if (preloadImages) {
			imageUrls.forEach((url, index) => {
				preloadImage(url, index);
			});
		}

		const interval = setInterval(() => {
			selectedImageIdx = (selectedImageIdx + 1) % imageUrls.length;
		}, duration);

		return () => clearInterval(interval);
	});
</script>

{#each imageUrls as imageUrl, idx (idx)}
	<div
		class="image w-full h-full absolute top-0 left-0 bg-cover bg-center transition-opacity duration-1000"
		style="opacity: {selectedImageIdx === idx ? 1 : 0}; background-image: {imagesLoaded.has(idx) ||
		!preloadImages
			? `url('${imageUrl}')`
			: 'none'};"
	>
		{#if preloadImages && !imagesLoaded.has(idx) && selectedImageIdx === idx}
			<!-- Loading placeholder for current image -->
			<div
				class="w-full h-full bg-gray-200 dark:bg-gray-700 animate-pulse flex items-center justify-center"
			>
				<svg class="w-12 h-12 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
					<path
						fill-rule="evenodd"
						d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z"
						clip-rule="evenodd"
					/>
				</svg>
			</div>
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
