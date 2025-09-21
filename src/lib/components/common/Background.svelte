<script lang="ts">
	import { config, selectedFolder, settings } from '$lib/stores';
</script>

{#if $selectedFolder && $selectedFolder?.meta?.background_image_url}
	{#if $selectedFolder?.meta?.background_image_url?.toLowerCase().endsWith('.mp4') || $selectedFolder?.meta?.background_image_url?.toLowerCase().endsWith('.webm')}
		<video
			class="absolute top-0 left-0 w-full h-full object-cover"
			autoplay
			muted
			loop
			playsinline
		>
			<source src={$selectedFolder?.meta?.background_image_url} type={$selectedFolder?.meta?.background_image_url?.toLowerCase().endsWith('.webm') ? 'video/webm' : 'video/mp4'} />
			Your browser does not support the video tag.
		</video>
	{:else}
		<div
			class="absolute top-0 left-0 w-full h-full bg-cover bg-center bg-no-repeat"
			style="background-image: url({$selectedFolder?.meta?.background_image_url})  "
		/>
	{/if}
{:else if $settings?.backgroundImageUrl ?? $config?.license_metadata?.background_image_url ?? null}
	{@const bgUrl = $settings?.backgroundImageUrl ?? $config?.license_metadata?.background_image_url}
	{#if bgUrl?.toLowerCase().endsWith('.mp4') || bgUrl?.toLowerCase().endsWith('.webm')}
		<video
			class="absolute top-0 left-0 w-full h-full object-cover"
			autoplay
			muted
			loop
			playsinline
		>
			<source src={bgUrl} type={bgUrl?.toLowerCase().endsWith('.webm') ? 'video/webm' : 'video/mp4'} />
			Your browser does not support the video tag.
		</video>
	{:else}
		<div
			class="absolute top-0 left-0 w-full h-full bg-cover bg-center bg-no-repeat"
			style="background-image: url({bgUrl})  "
		/>
	{/if}

{/if}